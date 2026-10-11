# QA independiente M2/T03 — compositor puro CPU

**VERDE en el alcance de T03 puro. DONE_WITH_CONCERNS: M2 no aceptado.** Windows y Docker Linux ejecutan 274/274 casos cada uno: 91 composición y183 regresión T02, 0 failed/error/skipped/flaky/interrupted. Son los mismos274 IDs únicos, no548 comportamientos distintos. Review2 A/B sin gaps conserva su propia evidencia; esta QA es nueva e independiente.

## Fuentes y reproducción

Runtime SHA256 `f2b5a79fcb4d489bc2155393adae6abf12049dda15836bd6960f24a806c312d3`; tests `2c5464e94390d73dfc36a67098a71f17ff09516bb89029550ef906ef7e611861`. Snapshot privado97 archivos autenticados antes y después en ambas plataformas. Los módulos app/tests realmente importados proceden del snapshot y quedan hashados en [Windows imports](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/windows/imports.json) y [Linux imports](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/linux/imports.json); los terceros/stdlib observados se separan en observed-tools.json. Versiones, intérprete, argv, PID y UTC de pytest constan en cada run.json. [Herramientas Windows y gates fijados](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/tools-pins.json).

Windows: entorno ROOT cargado mediante scripts/env.ps1 y `uv run --frozen --no-sync --all-packages python -X utf8 -B run-qa.py`. Linux: imagen existente por SHA256 `7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`, intérprete /studio/.venv/bin/python, fuentes actuales montadas /source readonly. No se prueba el backend histórico incluido en la imagen: imports actuales verifican el snapshot.

Contenedor propio UUID con --rm/--pull=never, UID:GID10001:10001, networknone, rootreadonly, cap-dropALL, no-new-privileges; snapshot y harness bindRO, output propio writable, /tmp tmpfs. Sin dispositivos GPU, build/pull/retag/admin/modelos/Ollama/servicios ajenos/BD activa. [Comando Docker y reap](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/linux.receipt.json); [inspect actual](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/image-current.stdout); [cleanup sin ID residual](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/container-cleanup.stdout). No se declara ext4 persistente ni prueba de durabilidad de almacenamiento.

La suite combinada se ejecutó una vez por plataforma, bajo coverage oficial, sin reintentos. --noconftest impide fixtures globales de BD; -p no:cacheprovider impide cachepytest. Warning único en ambas: cache_dir desconocido porque cacheprovider está desactivado; es diagnóstico de arnés, no flaky ni fallo de producto. No se creó RED en QA. No instalaciones.

## Resultado y cobertura whole

| Plataforma | Focal | Regresión T02 | Total único | Líneas composition.py | Ramas composition.py | Excluidas |
|---|---:|---:|---:|---:|---:|---:|
| Windows |91|183|274|546/576 =94,791667%|230/260 =88,461538%|0|
| DockerLinux CPU |91|183|274|546/576 =94,791667%|230/260 =88,461538%|0|

Coverage.py oficial mide el directorio creative completo con ambas suites, sin config heredada, exclude/omit ni promedios de plataformas para ocultar fallos. Cada plataforma supera80% líneas y ramas del archivo completo de producción. El directorio evita la exploración import-driven de NumPy observada previamente; no cambia producto ni elimina líneas. [JSON Windows](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/windows/coverage.json), [JSON Linux](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/linux/coverage.json), [cuentas exactas e IDs deduplicados](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/coverage-and-cases.json). El % combinado de líneas+ramas que coverage publica92,822967% se distingue de94,791667%líneas y88,461538%ramas.

Pytest/JUnit reales: [Windows](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/windows/junit.xml), [Linux](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/linux/junit.xml); streams completos [Windows](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/windows.stdout) y [Linux](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/linux.stdout). Ruff check y format--check de los dos archivos actuales exit0: [check](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/ruff-check.stdout), [format](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/ruff-format.stdout).

## Gate oficial

El adaptador propio transforma cada testcase JUnit real en un outcome individual: failure/error→failed, skipped→skipped, resto→passed. Exige274 IDs únicos y el mismo conjunto por plataforma. Sin retries ni stats inventados; qa-gate.py oficial recorre outcomes. Esto es unitCPU, **no Playwright ni E2E**. Inputs [Windows](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/windows/adapted-results.json), [Linux](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/linux/adapted-results.json), adapter íntegro en [run-qa.py](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/run-qa.py).

Windows qa-gate.py exit0:
```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 274,
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
Linux qa-gate.py exit0:
```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 274,
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

## Contrato18AC y trazabilidad

Cada AC del contrato cerrado tiene casos observados PASS en ambos JUnit. Los controles y facts son synthetic identificados; su validez estructural no acredita bytes/audio/master/modelo reales.

| Criterio | Resultado | Evidencia de test actual |
|---|---|---|
| AC01 | PASS Windows y Linux | 17 casos parametrizados; `test_ac01_trim_and_fade_counts` |
| AC02 | PASS Windows y Linux | 2 casos parametrizados; `test_ac02_decimal_half_up` |
| AC03 | PASS Windows y Linux | 6 casos parametrizados; `test_ac03_collapsed_region` |
| AC04 | PASS Windows y Linux | 3 casos parametrizados; `test_ac04_exact_numbers` |
| AC05 | PASS Windows y Linux | 4 casos parametrizados; `test_ac05_round_limits` |
| AC06 | PASS Windows y Linux | 9 casos parametrizados; `test_ac06_measured_duration` |
| AC07 | PASS Windows y Linux | 1 casos parametrizados; `test_ac07_anchored_bounds` |
| AC08 | PASS Windows y Linux | 2 casos parametrizados; `test_ac08_crossfade_dual_edges` |
| AC09 | PASS Windows y Linux | 11 casos parametrizados; `test_ac09_conversion_preflight_and_closed_facts` |
| AC10 | PASS Windows y Linux | 5 casos parametrizados; `test_ac10_empty_nominal_tail_is_real_dependency` |
| AC11 | PASS Windows y Linux | 2 casos parametrizados; `test_ac11_repaint_region_and_full_counts` |
| AC12 | PASS Windows y Linux | 4 casos parametrizados; `test_ac12_variations_and_cover_native_full` |
| AC13 | PASS Windows y Linux | 1 casos parametrizados; `test_ac13_extend_edges_and_measured_output` |
| AC14 | PASS Windows y Linux | 2 casos parametrizados; `test_ac14_full_keep_is_not_proven_copy` |
| AC15 | PASS Windows y Linux | 1 casos parametrizados; `test_ac15_frozen_nested_and_wrapper` |
| AC16 | PASS Windows y Linux | 18 casos parametrizados; `test_ac16_codec_replay_rejects_tampered_plan` |
| AC17 | PASS Windows y Linux | 1 casos parametrizados; `test_ac17_pure_wrapper_boundary` |
| AC18 | PASS Windows y Linux | 2 casos parametrizados; `test_ac18_sanitized_api_errors` |

T03 CA09/11/13/14/15: composición pura, índices/maps/pieces/facts/conversion/full-region/frozen wrappers/codec/replay/errores. E2E04/05/07 son trazas futuras del plan y **no ejecutadas** aquí. AC01 FIX1 acredita rechazo50+51>N100 y control50+50=N100 sin keepcentral; ambos corren en las dos plataformas.

[Ledger-lint actual](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/ledger-current.stdout) exit0, sin incoherencias duras. [Coverage-check global](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/coverage-check-global.stdout) exit0:0 broken_refs,0 tareas sin cobertura,24GWT enlazados,0 GWT huérfanos. Es trazabilidad del test-plan de M2, no prueba de ejecución de sus12E2E. El plan no se exime con marcador sinUI. No bloques API/A11Y autorizados. Constitución: producto local/puro, linaje inmutable y honestidad; no audio/SQL/GPU/publicación en esta QA.

## Preservación y límites

Guardas canónicas coinciden [antes](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/canonical-before.json)/[después](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/canonical-after.json); ambos archivos de producto siguen ausentes del canon. ROOT conserva la decisión CAS y el ledger. [Preservación](../../../../.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-20261011/preservation.json) revalida el candidato660 yFIX213 contra sus manifests sellados y las respuestas/hashcorrectión review2: no nueva captura antes de correr, sino autenticación post-QA contra los sellos previos. Fuentes97before/after y imports actuales son evidencia nueva. No escrituras en snapshot, canon, ledger, Git, locks ni memorias. Consulta knowledgepostexecution conservada; ningún flaky requirió diagnosis ni gotcha nuevo. Uso real tokens/eur/horasIA null.

PDF opcional omitido; no se instaló navegador/rasterizador ni se afirma revisión visual. El informe Markdown y evidencias son portables por enlaces relativos. No capturas UI porque no se ejercita UI. QA verde limitada al compositor puro; pendientes integración renderer/caller/custodia/publicación, audio real, capacidades y evaluación modelos, E2E04/05/07 y aceptación humana. No se cierra M2/spec ni se realiza handoffdocumenter global.

## Checklist manual del plan — pendiente

- [ ] M01 — Edición y fidelidad real de las uniones.
- [ ] M02 — Igualación A/B, decoder y transporte real.
- [ ] M03 — Cuatro capacidades musicales y30 generaciones propias.
- [ ] M04 — LLM elegido y Ollama compartido real.
- [ ] M05 — Custodia, manifiestos y replay persistente real.
- [ ] M06 — Provider opcional: revisión de privacidad y coste, real sólo si autorizado.
- [ ] M07 — Teclado, castellano, foco y utilidad.
- [ ] M08 — Puertas de calidad, compatibilidad y cierre.

ROOT puede evaluar adopción y cierre exclusivo T03 a partir de estos recibos; ningún hito íntegro aceptado. Al terminar el sello, este actor cesa escrituras para ROOTCAS.


## Adopción y cierre exclusivos de T03 por ROOT — 2026-10-11T16:01:36.792725+00:00

ROOTverifica168payload/97fuentes/imports/JUnit/gates/coberturaWindowsLinux/mismos274IDs únicos/imagenreadonlysinGPU/containerretirado. CAS2fuentesf2b5a79/2c5464e yVerificacióncanónica posterior91PASSexit0. T03purocompletado; M2 yE2E/audio/render/capacidades/modelos/manuales abiertos. Fuentes/evidenciasanteriores intactas. Consumo realnull.
