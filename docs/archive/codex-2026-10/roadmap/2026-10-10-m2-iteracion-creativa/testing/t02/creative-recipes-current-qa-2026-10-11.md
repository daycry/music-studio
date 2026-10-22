# QA actual T-02 — comprobación independiente de ROOT

ROOT verificó el sello privado de QA de 60 artefactos, 158 fuentes reales sin drift, verificación exacta183PASS, cobertura oficial183PASS/88,502269%0excl,3probes sinI/O, gates finales verdes y gate inicial rojo conservado. El alcance aceptable es sólo la unidadCPU; no prueba UI/E2E/música/SQL/render ni M1/M2 completos. La entrega técnica de QA de esta unidad CPU queda completa; ROOT registra su aceptación en el ledger tras verificar el PDF. M2 mantiene pendientes integración, interfaz y validación real.

Corrección documental trazable: el texto del informe original citaba por error `DID NOT RAISE RecipeError` como failure de los tres RED FIX2. Sus propios recibos/JUnit y red-causality-validation.json dicen `app.creative.recipes.RecipeError: RECIPE_INVALID`; esta copia corrige exclusivamente esa cita. Informe original SHA 95a882c3c7e3f81845128d5325f9bbeb9f49cd9a56131749b97ffd57f2b84dd4 y manifest60 intactos; ningún test/producto ni veredicto cambiado.

## Resolución de entrega por ROOT

La limitación de PDF del agente original queda resuelta mediante la skill `custom-agents:to-pdf`, Node gestionado y Chromium de Edge ya instalado. Dependencias y temporales permanecen en `.cache/tool-cache/to-pdf/` y en el namespace privado de ROOT; no se instala Python global, no se modifica producto ni sus locks, no se descarga Chromium. El paquete del conversor se usa exclusivamente para este artefacto de documentación.

El tema local corrige el desbordamiento de tablas: contenido A4 medido673px, ancho673px tras ajuste frente794px del tema original. Se inspeccionaron capturas del HTML en modo de impresión con la misma entrada y CSS; además se verifica el texto de todas las páginas del PDF con extracción UTF-8. Esa comprobación visual corresponde al HTML de impresión, no a una rasterización independiente del PDF.

La copia pública sustituye una ruta personal de caché por su descripción; el original privado conserva los bytes y SHA. La sección histórica «Artefactos y limitaciones de entrega» describe el momento de entrega del agente; su PDF pendiente ya está resuelto por ROOT. No cambia el veredicto de ningún test. [PDF del informe](creative-recipes-current-qa-2026-10-11.pdf).

## Informe independiente completo

# QA independiente — M2/T02 recetas privadas

**Veredicto final de unidad CPU: VERDE. M2 permanece NO aceptado.** Estado de entrega original: DONE_WITH_CONCERNS; ROOT publica el PDF de esta copia corregida por separado; el informe original se conserva íntegro.

## Alcance y autoridad

ADR-0037 permite unidades técnicas independientes conservando integración y aceptación real. Constitución §2 exige inmutabilidad e identidad; §3 conserva ledger único. ADR-0077 y recipe-contract-design §4.1–4.9 fijan captura/readers/proyección puras. Se leyeron brief, recibo ROOT, constitución, ADR-0037/0077, contrato, plan/test-plan y criterios/subtareas T02. T02 no crea jobs/takes/SQL ni ejecuta render, custodias, UI, mock, GPU, Ollama, servicios o red. No se lanzó una URL: guardrail local/privado no aplica a esta unidad sin host; ningún tercero se probó. No se alteró test-plan ni se marcó sin UI la iniciativa.

Ownership: exclusivamente este namespace. Fuentes, tests originales, ledger, Git y markers canónicos readonly. Entorno cargado scripts/env.ps1, uv gestionado con UV_OFFLINE=1/UV_NO_SYNC=1, Python3.12.14 del proyecto. COVERAGE_FILE, config, pytest cache y basetemp están aquí; PYTHONDONTWRITEBYTECODE=1.

## Ejecuciones propias

| Ejecución | Resultado | Evidencia |
|---|---|---|
| Verificación exacta `uv run pytest -q apps/server/tests/test_creative_recipes.py` |183 PASS, exit0, sin JUnit solicitado |[stdout](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/verification-exact.stdout.txt), [recibo](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/verification-exact.receipt.json)|
| Cobertura primer intento `--cov=app.creative.recipes` |1 ERROR colección, exit2/interrumpida |[stdout](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/coverage-tests.stdout.txt), [JUnit real](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/junit.xml), [recibo](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/coverage-tests.receipt.json)|
| Cobertura final por ruta `--cov=apps/server/app/creative --cov-branch --cov-fail-under=80` |183 PASS, 0 FAIL/ERROR/SKIP, exit0 |[stdout](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/coverage-tests-retry-path.stdout.txt), [JUnit real](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/junit-path.xml), [recibo](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/coverage-tests-retry-path.receipt.json)|
| Pruebas propias puras sin I/O |3 PASS, exit0 |[código](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/test_qa_pure.py), [stdout](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/pure-no-io.stdout.txt), [JUnit](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/junit-pure.xml)|
| Ruff check / format --check |0 / 0 |[check](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/ruff-check.stdout.txt), [format](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/ruff-format.stdout.txt)|
| ledger-lint / coverage-check referencial |0 / 0; 0 referencias rotas |[ledger](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/ledger-lint.stdout.txt), [referencias](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/coverage-reference.stdout.txt)|

La importación temprana añadida por cobertura modular produjo `ImportError: cannot load module more than once per process` en NumPy. El modo por ruta instrumenta los mismos dos archivos completos sin importación anticipada y termina conforme. Se preservó el JUnit rojo y se ejecutó su gate rojo; no se justifica flaky de producto ni se omite un test. Hubo un error posterior cp1252 al imprimir la salida UTF-8 del ledger: wrapper exit1; stdout nativo/recibo ledger0 preservados, diagnóstico reconstruido explícitamente en [harness-diagnostics.json](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/harness-diagnostics.json). Los siguientes wrappers usan UTF-8. Estos diagnósticos del arnés no prueban defecto del producto.

## Cobertura oficial

Paquete completo `creative/__init__.py` y `creative/recipes.py`, líneas+ramas: **88.502269289%**, excluidas **0**, umbral80%, gate0. No omit/exclusiones deliberadas; config `exclude_lines =` vacía. Total: 916 statements, 83 líneas no cubiertas, 406 ramas, 69 ramas no cubiertas. [JSON oficial](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/coverage-path.json), [gate](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/coverage-gate.json), [base oficial](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/coverage.db), [config](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/coverage-config.ini). La cobertura no acredita integración o audio.

## Adaptación explícita qa-gate CPU

El script oficial qa-gate.py se ejecutó sobre traducción del JUnit pytest REAL a stats/suites: cada testcase produce un resultado, failure/error se conservan rojos, ausencia/exit no cero/skips producen errors top-level. Se registran framework `pytest CPU`, hash original, cwd, inicio/fin, exit y conteos; nunca se afirma Playwright. No se inventan suites UI ni reintentos exitosos de tests fallidos. [Adaptación final y provenance](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/qa-gate-final-cpu.adapted.json), [adaptación roja](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/qa-gate-initial-error.adapted.json), [script](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/finish-evidence.py).

Gate final (solo unidad CPU):

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 183,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

Gate original error preservado:

```json
{
  "verdict": "NO-VERDE",
  "reason": "el runner reportó errores de ejecución",
  "errors": [
    "pytest exit=2; errors=1; skipped=0; actual cases=1"
  ]
}
```

Los3 probes propios tienen gate separado0. No suman ejecuciones repetidas a183 tests focales. Los tres RED causales FIX2 fueron inspeccionados como historia, no como greens de QA: failure `app.creative.recipes.RecipeError: RECIPE_INVALID`, exit1, runtime FIX1 preimagen65a5e8b…, testsadd3236e…, tres tipos integer/string/array. [Validación de recibos y JUnit](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/red-causality-validation.json).

## Matriz de criterios de unidad

| Criterio T02 / contrato | Evidencia ejecutada propia | Pendiente fuera unidad |
|---|---|---|
| CA unidad1: mutación nested no cambia bytes/hash; extras/secrets/NaN/IDs/refs rechazadas |183 focales: capture_freezes_nested_context, params_and_descriptor_are_deeply_frozen, mapping_callers_are_copied, cpu_rejects_invalid_context, each_nested_dto_is_closed, frozen_json_rejects_non_json, legacy_secret_keys_sanitized/secret_blobs_rejected |Revalidar bytes y propiedad del archivo real en admisión|
| CA unidad2: todos padres/campos efectivos; legacy sin rewrite |crossfade_keeps_both_parents_and_composite_authorship, variation_request_conserves_selected_effective_output, vocal_variation_preserves_exact_effective_lyrics_and_authorship, legacy_preserves_raw_and_absence, legacy_snapshot_job_requests_preserve_presence, descriptor_namespace_defaults_and_read_do_not_rewrite |SQL/DAG/linaje/publicación durable y root transitiva reales|
| CA unidad3: verificación propia y gates de unidad |exact183, cobertura183/gate80, Ruff0/format0, qa-gate0; revisionesROOT previasA/B0 gaps sólo contexto, no sustituyen ejecución propia |ROOT comprueba entrega y decide estado; QA no toca ledger|
| Schema cerrado union/open/implicit y B03 explicitnonobject |schema_object_union_must_be_closed; schema_admitting_objects_still_requires_explicit_closure; schema_object_keywords_do_not_close_explicit_nonobjects; schema_explicit_nonobject_types_remain_validated; internal_pointer/local_ref/literal_values negativos y positivos |Exportar schema en T04|
| Privacidad errores |private_error_does_not_retain_pydantic_context, dynamic_descriptor_named_key_cannot_hide_credentials y negativos secretos; no repr privado emitido |Mapping HTTP posterior|
| Pureza no I/O en alcance |3 pruebas propias bloquean builtins.open/io.open/Path.open/socket/Popen/sqlite.connect después de import/setup: capture/read trim, inference y crossfade; proyección real inference también |Import del paquete app tiene dependencias reales; no afirmar aislamiento global de app ni equivalencia de integración|
| CA-07,CA-09,CA-11,CA-15,CA-29 de spec vinculadosT02 |Unidad aporta captura/proyección/antecedentes/derechos para estosCA; coverage-check verifica referencia |E2E03/04/05/07 y aceptación integral requieren las otras tareas; NO acreditados por CPU|

No se crearon tests espejo ni stubs de dependencias. Las pruebas propias reutilizan sólo generadores de datos sintéticos del test original, importando clases/helpers runtime reales. El bloqueo de I/O es un detector, no un sustituto de dependencias. Captura pureza limitada a operaciones ejecutadas tras import; no prueba todas las rutas posibles.

## Fuentes y preservación

158 pinsROOT before/after/final idénticos: [before](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/sources-before.json), [after](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/sources-after.json), [final](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/sources-final.json). Cuatro identidades directas: recipes d8eb0512…, tests add3236e…, documento d06280be…, init89823ef1… (hashes completos en guardas). Imports efectivos comprobados en proceso propio con mismo cwd e intérprete: recipes,queue.inputs,resolver,worker.contracts,engine_contract, todos rutas canónicas/hashes declarados y reales, sin copias ni fakes: [probe](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/imports-probe.py), [salida](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/imports.stdout.txt), [recibo](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/imports.receipt.json). Se prueba resolución/import real en ese proceso, no se afirma una captura interna de módulos de la pasada pytest previa.

Preservación verificada SHA/tamaño según bases correctas: original219 y FIX2136 namespace relativo, FIX1244 relativo repo; snapshots revisiones1–3 cada158 contra pins de su recibo. [Detalle completo](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/preservation.json). Ninguna evidencia histórica escrita.

## Puertas deterministas referenciales

Ledger:

```text
⚠️  T-02: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-03: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-04: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-05: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-06: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-07: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-08: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-09: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-10: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-11: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-12: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-13: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-14: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-15: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-16: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-17: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-18: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-19: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-20: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-21: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-22: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-23: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-24: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-25: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-26: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-27: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-28: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-29: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-30: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
ledger-lint: 0 incoherencias · 29 avisos (tasks.md)
```

Coverage-check:

```json
{"applies": true, "defined": ["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "E2E-12", "M-01", "M-02", "M-03", "M-04", "M-05", "M-06", "M-07", "M-08"], "referenced": ["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "E2E-12", "M-01", "M-02", "M-03", "M-04", "M-05", "M-06", "M-07", "M-08"], "broken_refs": 0, "tasks_sin_cobertura": [], "tests_sin_referencia": [], "gwt_cubiertos": ["CA-02", "CA-03", "CA-04", "CA-05", "CA-06", "CA-07", "CA-08", "CA-09", "CA-10", "CA-11", "CA-12", "CA-13", "CA-14", "CA-15", "CA-16", "CA-17", "CA-18", "CA-20", "CA-22", "CA-25", "CA-26", "CA-27", "CA-28", "CA-30"], "gwt_sin_cubrir": [], "gwt_sin_id": 0, "test_plan_na": false, "marcador_no_canonico": null}
```

Referencias conformes no significan E2E ejecutados ni cobertura funcional global. test_plan_na=false; no gap de referencias en esta ejecución.

## Checklist pendiente de M2

- [ ] E2E-03: variación de petición/audio en UI/API y estado persistido.
- [ ] E2E-04: extensión en UI/API, conservación y resultados.
- [ ] E2E-05: región/repaint en UI/API y resultado real.
- [ ] E2E-07: edit/crossfade real, audio y publicación durable.
- [ ] M-01 a M-08 del test-plan integral: todos pendientes en este informe; escuchar/medir/comprobar con persona e infraestructura real cuando corresponda.

No app/UI/mock/SQL/render/modelo ejecutados; ninguna canción ni archivo de datos se tocó. Sin screenshot por unidad sin UI, no screenshots ficticios. La UI M2 sigue pendiente. Sin handoff documenter, cambios de estados o Jira/Confluence. [Cleanup](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/cleanup.json) registra cero recursos/servicios creados y ningún borrado; temporales de evidencia retenidos en namespace.

## Artefactos y limitaciones de entrega

report.md generado aquí. **report.pdf no generado:** la herramienta to-pdf habitual no existe en `.cache/tool-cache/to-pdf/` ni en la caché externa habitual del conversor; instalación prohibida por ROOT, no se descargó nada. ROOT resolverá el artefacto al incorporar el informe. No se atribuye un PDF inexistente. La habilidad to-pdf se leyó para comprobar sus requisitos; no se aplicó instalación.

Manifest final lista bytes/SHA de todos los artefactos, excluyendo manifest y recibo final para evitar autorreferencia. Métricas tokens/horasIA/coste reales: null; no inferidos de duración. Entrega **DONE_WITH_CONCERNS** por PDF, unidad CPU técnicamente conforme; **T02/M2 no cerrados por este agente**.

Consulta gotchas de proyecto sin coincidencias; fallback listado completo ejecutado y guardado en [recibo](../../../../../.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-20261011/knowledge-fallback.receipt.json). No se escribió conocimiento ni se prometió historial.
