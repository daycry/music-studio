---
status: SCOPED_CURRENT_NATIVE_QA_PASS
scope: ADR0050 isolated process/runtime dependency
test-plan: n/a (sin UI)
actual-model: null
actual-tokens: null
actual-EUR: null
actual-IAhours: null
---

# QA2 independiente T-09

**SCOPED_CURRENT_NATIVE_QA_PASS**. JUnit original: 76/76 PASS, 0 errores, 0 failures, 0 skips; exit real 0. PDH explícitamente deseleccionado con `-k not real_native_raw`; no silent skip. Una sola ejecución completa vigente, sin smoke previo. Argv/UTC/executable/entorno y salidas originales en baseline/launch.json, completion.json, stdout.txt, stderr.txt; accounting propio adjunto.

QA1 permanece readonly: report/log/JUnit reales 42 PASS y34 setup errors por import ausente de test_benchmark_observation. Sólo el bootstrap propio QA2 incorpora scripts/eval/tests para resolver el helper original exacto. Producto y tests canónicos no modificados. Instrumentación copiada e inspeccionada, rutas exclusivas QA2; no ejecución de runners históricos. Copias byte/AST exactas de ambos tests, assertions/decoradores/parametrización/funciones intactos;21 funciones process y16 runtime legacy AST exactas, sin claim global. El helper de observación y todos los scripts/eval se archivaron antes de imports; sensor_values/factorías/imports/bootstrap/test/wrapper/runner efectivos se archivan antes de cada nacimiento.

AGENTS, CONTINUE-HERE, constitución, brief y agents/qa.md custom-agents1.22.0 leídos; adaptación CPU autorizada. Review5-fix1 report/receipt/official launch/JUnit/coverage e inventory contrastados, review6A/B y adjudicación0gaps leídos. Inventario predecessor 11320 entradas verificado readonly, mismatches 0. QA1 setup y las reservas anteriores no se retroperfeccionan. Early RED UTC/closure incompletas, incidente histórico payload/launcher rescatado/missingcleanupUNKNOWN y primera combinación parent-only conservan sus limitaciones.

## Fuentes y cobertura actual

69 protegidos, drift 0. Fuentes process d1d055/runtime b84ce9/test ec70ab exactas respecto al freeze root antes/después; process original sin cambio. Helpers antes/después registrados. Caches/env/tmp/pytest/coverage privados creados antes de imports, env.ps1 cargado y overrides restaurados; Python gestionado del repo. Sin hostPython/install/network/Docker/GPU/WSL/Ollama/UI/PDH/knowledge/subagentes. Únicamente paths QA2 escritos; ledger/Git/decisiones/aceptación/meter exclusivos root.

Cobertura WHOLE EACH con líneas+branches, cero exclusiones, exclusivamente padre nuevo y 106 bases nativas nuevas de esta misma ejecución sobre bytes congelados. Nombres explícitos en coverage-inputs.json; originales padre/hijos/combined/coverage-original.json conservados. No unión de QA1/histórico, ni promedio, ni exclusión de módulos ausentes.

```json
{
  "scripts\\eval\\benchmark_canonical_runtime.py": {
    "covered_lines": 614,
    "num_statements": 684,
    "percent_covered": 85.33916849015317,
    "percent_covered_display": "85",
    "missing_lines": 70,
    "excluded_lines": 0,
    "percent_statements_covered": 89.76608187134502,
    "percent_statements_covered_display": "90",
    "num_branches": 230,
    "num_partial_branches": 64,
    "covered_branches": 166,
    "missing_branches": 64,
    "percent_branches_covered": 72.17391304347827,
    "percent_branches_covered_display": "72"
  },
  "scripts\\eval\\benchmark_process.py": {
    "covered_lines": 383,
    "num_statements": 443,
    "percent_covered": 81.58319870759289,
    "percent_covered_display": "82",
    "missing_lines": 60,
    "excluded_lines": 0,
    "percent_statements_covered": 86.45598194130926,
    "percent_statements_covered_display": "86",
    "num_branches": 176,
    "num_partial_branches": 50,
    "covered_branches": 122,
    "missing_branches": 54,
    "percent_branches_covered": 69.31818181818181,
    "percent_branches_covered_display": "69"
  }
}
```

## Evidencia nativa acotada

108 launch propios, 107 asignaciones observadas, 108 cleanup; disposiciones {"CLOSED_CONFIRMED": 91, "UNKNOWN_QUARANTINED": 17}. 17013 copias fuente por nacimiento verificadas. UUID/argv/UTC previos a Popen y PID posterior; FILETIME/Job reales por assign passthrough donde se obtuvo asignación. Rechazos/partials no se cuentan como births perfectos. Sin constructor/controller/validator/ownership doubles: observación passthrough Popen/assign/cleanup/deliver y wrapper coverage que delega IO original. stdout hijo RPC real; stderr DEVNULL UNKNOWN. Excepciones wrapper son evidencia separada.

Recursos propios vivos observados 0, missingcleanup UNKNOWN 0, contradicciones de evidencia confirmed 0. Errores negativos/partials conservan UNKNOWN_QUARANTINED aunque Job vacío o proceso terminado. Recibos y errores originales en native-ownership-cleanup.json. Closedrepeat sólo donde ejecutado por test original, igualdad del receipt comprobada por assertions canónicas originales; el hook _cleanup no observa otra llamada interna en este trace (repeat_cleanup_calls vacío). Ningún control foreign Job/PID/handle terminado por el actor; controles propios se limpian en finally original.

Los tests actuales ejecutados distinguen handlers sintéticos/policy/mocks de procesos Windows reales: el positivo64 retiene collector mientras admite64frames+terminal y completa ingest legítimo concurrente; canonical State/Store real,8witnesses y noveno ingest prioritario. Controles de MAC/binding/seq/lane/type/index/framebyte/65quota verifican admisión acotada; el sobredimensionado directo al receptor es control sintético, no frame nativo. Constructor opt-in Python trusted, nunca consumerJSON; claves MAC no se registran en logs/env/argv/files. Two lanes/one pending each/writer2, fragment1200/frame262144/64progress, deadline2s original no renovado/reserve250ms/cleanup220ms observados en código y casos canónicos. Deadline/failure tras progreso conserva frames/partialraw/causa; cleanup secundario no reemplaza primario. RAW/epochs/ownership desconocidos permanecen desconocidos, sin tickets inventados. Bootstrap sameleaf/parent/context/source prebound y PID/FILETIME/Job anteriores a capture según asserts originales.

Watchdog knownJob con pipe/WinEvent/IO passthrough real acredita límites en host ordinario. Los readers/writers bloqueados se unen tras aborto del Job propio antes de resources_returned; falta EOF conserva UNKNOWN. Bloqueo físico zero-byte CustodyStore.ReadFile **UNTESTED**. Sin claim de preemption nativa general, GPUcadence/control del benchmark completo.

## Verificaciones reales

TDD n/a QA independiente; predecessor RED readonly. Scoped Ruff/checkformat, ledgerlint readonly y coverage-check original:


`ruff-check` exit 0, argv/UTC en accounting, stderr original `ruff-check-stderr.txt`:

```text
All checks passed!
```

`ruff-format` exit 0, argv/UTC en accounting, stderr original `ruff-format-stderr.txt`:

```text
4 files already formatted
```

`ledger-lint` exit 0, argv/UTC en accounting, stderr original `ledger-lint-stderr.txt`:

```text
⚠️  T-09: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-10: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-11: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-12: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-13: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-16: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-20: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  línea 2277: cabecera de revisión no casa con REVISION_HDR_PATTERN: jira-flow/task-brief no la verán — usa `## Revisión de dos lentes — intento N: <resumen>` (`##` exacto, sin paréntesis tras N)
ledger-lint: 0 incoherencias · 8 avisos (tasks.md)
```

`coverage-check` exit 0, argv/UTC en accounting, stderr original `coverage-check-stderr.txt`:

```text
ℹ️  test-plan: n/a (sin UI) declarado en improvement-plan.md: iniciativa sin UI por diseño, la puerta de cobertura NO se ha ejecutado (no es «cobertura OK»)
ℹ️  se listan para la revisión 21 tarea(s) del ledger (la spec no aporta criterios rastreables) (T-00, T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10, T-11, T-12, T-13, T-14, T-15, T-16, T-17, T-18, T-19, T-20): la puerta no exigía cobertura de estos (solo la exige de los [GWT]), así que aquí no se exime nada — su evidencia es el campo `Verificación` de la tarea que los cierra en tasks.md
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19", "T-20"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

Ledger: siete warnings históricos Changelog cualificados; cualquier aviso adicional se conserva en la salida real. Sin UI por diseño (`test-plan: n/a (sin UI)`): puerta documental no ejecuta cobertura E2E; lista eximidos y eximidos_exigidos original arriba. Sin Playwright/PDF/E2E inventados ni aceptación global del test-plan.

Episode/callers/coordinator/rowtickets/prereq/sourceCLI/FINALpacks/restore/fullintegration/matriz160/cadencia13h/calibración/GPU/calidad permanecen dependencias futuras. Root decide aceptación/Git/ledger/meter; estimado1.5, consumos reales NULL. Inventario NONCLI completo excluye sólo cuatro nombres top reservados y su propio fichero; CLI activa no sellada.


QA1 inventario readonly verificado: 5282 entradas, cero cambios; fichero root-custody posterior al inventario cualificado, sin replay. Instrumentación Python AST exacta y launcher/config exactos salvo rutas propias; prepare cambia sólo import path privado. Helper original test_benchmark_observation byte exacto archivado antes de imports. Ledger real:0 incoherencias/8avisos (7Changelog históricos+1cabecera revisión). Final108launch/108Popen/107assign/108cleanup:91CLOSED_CONFIRMED/17UNKNOWN_QUARANTINED; un rechazo de assign conserva ausencia de birth observado. Cuatro errores cleanup de controles negativos detallados en recibo, no todos cero.
