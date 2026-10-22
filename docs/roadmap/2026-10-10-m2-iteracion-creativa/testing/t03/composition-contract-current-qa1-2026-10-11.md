# Informe de QA — M2/T03, contrato documental privado

| Campo | Resultado |
|---|---|
| Fecha | 2026-10-11 |
| Estado alcance | VERDE documental 60/60; producto T03/M2 pendiente |
| URL / guardrail | Prosa, sin HTTP ni hosts auditados |
| Plan/test-plan | Snapshot readonly; test-plan global M2/UI conservado |
| Fuentes | Contrato borrador, ADR propuesta; incorporación sólo ROOT |

## Veredicto (qa-gate)

Script oficial exit0. Entrada documental adaptada con outcomes reales: **no Playwright ni pytest**. E2E ejecutados: 0.

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 60,
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

## Resumen

60 checks pasan: 26 pins y 13 controles aritméticos propios incluidos. Los 18 AC son matriz futura revisada, no pruebas de producto pasadas. TDD/cobertura n/a: prosa. Verificación focal uv run pytest -q apps/server/tests/test_creative_composition.py pendiente: compositor no implementado. Sin cierre T03/M2 ni handoff documenter.

Diagnóstico original59/60/gate1 conservado en diagnostic-attempt1/: búsqueda sensible a mayúsculas ("No prueba…"). Corregido sólo harness a casefold, fuentes exactas. No fallo contractual ni flaky producto.

## Cobertura y ledger

qa-ledger exit0: 0 incoherencias, 29 avisos (Changelog faltante/cabecera revisión incluidos). qa-coverage exit0: broken_refs0, tasks_sin_cobertura[], tests_sin_referencia[], gwt_sin_cubrir[], test_plan_na=false. Cobertura declarada, no ejecución/exención global sin UI.

## Resultados documentales y aritméticos

| Check | Resultado | Evidencia |
|---|---|---|
| AC matrix | PASA | 18 future acceptance cases, not executed product tests |
| Control matrix | PASA | 13 independent arithmetic controls below |
| States and choice | PASA | private draft/proposal; no product acceptance |
| Closed spans and nominal scope | PASA | nominal only converted B; strict render/dst; complete scope |
| Closed replay/facts/error policies | PASA | documentary specification only |
| Shape and grid bounds | PASA | local engine region vs global parent, full construction counts |
| Unimplemented boundaries | PASA | no render, audio, publication or API evidence attributed; case insensitive prose match |
| Links six-document scope | PASA | 120 enlaces; detalle completo en document-checks.json |
| Index integration | PASA | index mentions proposed ADR |
| Global test-plan preserved | PASA | M2 UI/E2E remains applicable |
| Arithmetic C01 | PASA | {"computed": [21, 72, 51], "expected": [21, 72, 51], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C02 | PASA | {"computed": [11, 21, 79], "expected": [11, 21, 79], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C03 | PASA | {"computed": [21, 159], "expected": [21, 159], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C04 | PASA | {"computed": [105, 45], "expected": [105, 45], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C05 | PASA | {"computed": [25, 105], "expected": [25, 105], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C06 | PASA | {"computed": [110], "expected": [110], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C07 | PASA | {"computed": [40, 110], "expected": [40, 110], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C08 | PASA | {"computed": [140, 40], "expected": [140, 40], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C09 | PASA | {"computed": [25], "expected": [25], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C10 | PASA | {"computed": [40, 20, 161], "expected": [40, 20, 161], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C11 | PASA | {"computed": ["001"], "expected": ["001"], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C12 | PASA | {"computed": [160, 80, 101, 1], "expected": [160, 80, 101, 1], "origin": "independent stdlib arithmetic, no composer"} |
| Arithmetic C13 | PASA | {"computed": [100], "expected": [100], "origin": "independent stdlib arithmetic, no composer"} |
| 81/80/79 converted tail | PASA | 79 rejects before output; 99 is not a valid output plan |
| Half-up and collapse | PASA | ties, exponent, signed zero, collapse |
| Endpoint outside rational | PASA | N=1/rate=3; equality anchor accepted, nextafter rejected independently of rounding |
| Full minima | PASA | full repaint/extend minimum one generated frame |
| Envelope minimum and complement | PASA | K=7 complementary rational ramps; K=1 forbidden by document, not runtime tested |
| MAX no materialization | PASA | large arithmetic only; no audio allocation |
| T02 immutable apps/server/app/creative/recipes.py | PASA | byte exact snapshot/canonical; no import or query |
| T02 immutable apps/server/app/creative/__init__.py | PASA | byte exact snapshot/canonical; no import or query |
| T02 immutable apps/server/tests/test_creative_recipes.py | PASA | byte exact snapshot/canonical; no import or query |
| Independent ledger lint | PASA | qa-ledger.stdout |
| Global declared traceability | PASA | qa-coverage.stdout; declared coverage, not execution |

Racionales estándar independientes, sin importar compositor: C01–C13, cola81/80/79, mínimos full80/81, extremo1/3+nextafter, signed zero/exponentes, límite entero, rampas complementarias. Validaciones runtime, errores sanitizados/replay/inmutabilidad DTO se revisan como contrato: implementación/ejecución pendiente.

Nominal_src sólo B convertido, src literal separado, render/dst estrictos y scope completo. C12 conserva cola positiva/nominal vacío; Bc80 omite cola y Bc79 rechaza bounds. C13 separa región global padre/buffer region local; full valida counts target. FIX1 espera ratificación ROOT. Claims full declared_keep_unverified: T08 contrastará PCM/clipping/FFmpeg/soxr real. No comprobación real de licencia/capacidad.

## Resultados automáticos (E2E)

No ejecutados. E2E04/05/07 pendientes; sin screenshots UI/audio/jobs/attempts/takes fabricados.

## Checklist manual pendiente

- [ ] **M-01 — Edición y fidelidad real de las uniones**: pendiente global M2, consultar test-plan.
- [ ] **M-02 — Igualación A/B, decoder y transporte real**: pendiente global M2, consultar test-plan.
- [ ] **M-03 — Cuatro capacidades musicales y30 generaciones propias**: pendiente global M2, consultar test-plan.
- [ ] **M-04 — LLM elegido y Ollama compartido real**: pendiente global M2, consultar test-plan.
- [ ] **M-05 — Custodia, manifiestos y replay persistente real**: pendiente global M2, consultar test-plan.
- [ ] **M-06 — Provider opcional: revisión de privacidad y coste**: pendiente global M2, consultar test-plan.
- [ ] **M-07 — Teclado, castellano, foco y utilidad**: pendiente global M2, consultar test-plan.
- [ ] **M-08 — Puertas de calidad, compatibilidad y cierre**: pendiente global M2, consultar test-plan.

- [ ] ROOT ratifica FIX1/incorpora canon si procede.
- [ ] Producto T03: RED-GREEN, negativos/DTO/replay, verificación focal/review/QA/cobertura cambiada>=80%.
- [ ] T08: conversión/render real, pins/licencia/capacidad, mediciones/recibos. T04/T07: proyección convert/publicación/custodia.

## Trazabilidad y preservación

| Tarea | Actual | Pendiente |
|---|---|---|
| T03 / CA09,11,13,14,15 | 18AC/13 controles, links/aritmética/policies | Producto/E2E04/05/07 |
| T02 | Tres archivos byte exactos snapshot/canon | No tests reejecutados/atribuidos |
| M2 | Ledger/cobertura declarada | Hito/aceptación humana |

Before/after: {"snapshot": [], "canonical": ["docs/roadmap/2026-10-10-m2-iteracion-creativa/tasks.md"]}. tasks.md canónico actualizado por ROOT durante despacho (recuperación/cabecera): divergencia esperada, no defecto ni restauración. Snapshot26 exacto. Dos fuentes nuevas/cuatro docs integración revisados, links/estado/índice. Links ausentes snapshot resueltos sobre canon readonly; procedencia registrada.

## Evidencias y PDF

- [Checks](../../../../../.cache/dev-cycle/m2/creative-composition-t03-contract-current-qa1-20261011/document-checks.json), [entrada adaptada](../../../../../.cache/dev-cycle/m2/creative-composition-t03-contract-current-qa1-20261011/documentary-gate-input.json), [gate](../../../../../.cache/dev-cycle/m2/creative-composition-t03-contract-current-qa1-20261011/qa-gate.stdout).
- [Ledger](../../../../../.cache/dev-cycle/m2/creative-composition-t03-contract-current-qa1-20261011/qa-ledger.stdout), [cobertura declarada](../../../../../.cache/dev-cycle/m2/creative-composition-t03-contract-current-qa1-20261011/qa-coverage.stdout); receipts argv/cwd/UTC/exits/SHA streams.
- [Before](../../../../../.cache/dev-cycle/m2/creative-composition-t03-contract-current-qa1-20261011/before.json), [after](../../../../../.cache/dev-cycle/m2/creative-composition-t03-contract-current-qa1-20261011/after.json), [ROOT](../../../../../.cache/dev-cycle/m2/creative-composition-t03-contract-current-qa1-20261011/release-root.receipt.json), manifest final excluye autorreferencia.
- PDF to-pdf/dependencias existentes/Edge headless/perfil privado, sin instalación. Preview print HTML y estructura PDF. **Limitación:** preview no rasteriza PDF final; no inspección visual de todas sus páginas.

Sin GPU/Ollama/red/servicios producto/SQL/datos/Git/canon/ledger escritos. Uso real unknown/null; tier no acredita modelo efectivo.


## Ratificación de ROOT

2026-10-11T14:46:46.675900+00:00:84archivos inventariados,26fuentes,60checks reales,entrada adaptada/streams/recibos/gate oficial verificados. Revisión2 A/B sin gaps, cuatro anteriores corregidos. ContratoO1/ADR0079 incorporados; no productoT03ni cierreM2. El informePDF privado tiene6páginas comprobadas estructuralmente y previewprint inspeccionado, sin rasterizaciónfinal. Evidencias y PDF original permanecen en namespaceQA privado sin atribuirlas a audio/E2E.
