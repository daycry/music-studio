# QA independiente M2/T02 — contrato documental previo al RED

UTC: 2026-10-11T11:26:02.024529+00:00. Resultado: **PASS DOCUMENTAL**, 18/18 comprobaciones documentales.

Adaptación explícita: qa-gate.py recibe documentary-gate-input.json derivado exclusivamente de checks reales de este script y sus recibos. No es un reporter Playwright, test de producto ni porcentaje de cobertura. Capture/readers/projection aún no implementados. TDD n/a: prosa; cobertura producto n/a. Constitución §2: historia y hashes intactos; §3: estado exclusivamente ledger; §4: privacidad y derechos.

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 18,
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

Gate exit: 0. Evidencia: qa-gate.receipt.json, qa-gate.stdout, qa-gate.stderr. Entorno scripts/env.ps1 + uv --frozen --all-packages; intérprete efectivo .venv/Scripts/python.exe. No imports de app.

| ID | Resultado | Comprobación | Evidencia |
|---|---|---|---|
| DOC-01 | passed | Snapshot 36/36 authenticated | cases.json; line references and command receipts |
| DOC-02 | passed | Canonical 34/34 guards authenticated with fusion tasks hash | cases.json; line references and command receipts |
| DOC-03 | passed | Review receipts, five-doc diff, proposal isolation and T02 open | cases.json; line references and command receipts |
| DOC-04 | passed | Relative links from future canonical destinations through overlay | cases.json; line references and command receipts |
| DOC-05 | passed | Envelope version and canonical wire/limits | cases.json; line references and command receipts |
| DOC-06 | passed | Eight operation variants and CPU/inference identity | cases.json; line references and command receipts |
| DOC-07 | passed | Frozen wrappers, strict schemas and separate capture/reader | cases.json; line references and command receipts |
| DOC-08 | passed | Engine required/roles/media compatibility and explicit FLAC/WAV negative | cases.json; line references and command receipts |
| DOC-09 | passed | Canonical recipe intention and future measured results consistent | cases.json; line references and command receipts |
| DOC-10 | passed | Effective historical request basis, seeds and lyric lineage | cases.json; line references and command receipts |
| DOC-11 | passed | Owner/IDs/parent references, roots and asset rights | cases.json; line references and command receipts |
| DOC-12 | passed | Pins are selections and preserve false runtime verification | cases.json; line references and command receipts |
| DOC-13 | passed | Legacy raw bytes, omitted/null fields and isolated M1 codecs | cases.json; line references and command receipts |
| DOC-14 | passed | Privacy policy namespaces and separate PEM/Bearer/URI rules | cases.json; line references and command receipts |
| DOC-15 | passed | Authority delegated, schemas/runtime/TDD and open questions outside T02 | cases.json; line references and command receipts |
| DOC-16 | passed | Ledger lint actual: hard errors zero; retain warnings | cases.json; line references and command receipts |
| DOC-17 | passed | Coverage references actual for full M2 plan, no global no-UI exemption | cases.json; line references and command receipts |
| DOC-18 | passed | Sources before/after and snapshot unchanged | cases.json; line references and command receipts |

## Puertas y trazabilidad

ledger-lint: 0 incoherencias y 29 avisos Changelog (T02..T30 abiertas), exit0. Coverage-check: 0 referencias rotas, 24 GWT con escenario, 0 tareas sin referencia y 0 escenarios huérfanos, exit0. Las salidas completas siguen abajo. Coverage-check comprueba referencias del test-plan M2 con UI futura: no ejecuta esos escenarios ni mide cobertura de código. La unidad contractual tiene cinco documentos y cero UI. No se marca el hito como sin UI.

T02 conserva seis casillas pendientes (tres criterios y tres subtareas), en-progreso. Ningún CA de T02/M1/M2 cerrado. E2E-03/04/05/07 y M-xx del plan íntegro siguen pendientes de ejecución con producto. Ratificación/adopción nueva pertenece a ROOT después de esta QA. O1 elegido bajo delegación no es aceptación del contrato detallado ni M2.

## Evaluación y límites

Las ocho variantes mantienen una receta por toma, antecedentes identificados y texto/hash/autoría históricos. FrozenDescriptor exige cierre recursivo y namespace distinto de las guardas M1; captura nueva materializa defaults una vez y lectura conserva payload sellado. Proyección exige required, roles únicos/conocidos y media exacta, con negativo FLAC/WAV sin retag/conversión/SHA ficticio. Los mapas sellados son intención; T03 y autoridad/publicación posterior acreditarán muestras y resultados medidos. Legacy conserva ausencias/null/raw con límite propio. Las preguntas abiertas CPU plan/recibo/publicación son posteriores y no dejan DTO/firmas T02 pendientes.

Estas comprobaciones estructurales/textuales acompañan lectura documental; no ejecutan dichos comportamientos. No prueban inmutabilidad real, rechazo runtime, capacidad de engine, audio, derechos legales, custodia, permisos, SQL, GPU ni migraciones. No hubo Playwright/URL/PDF/red/instalaciones/Docker/WSL/GPU/BD ni Git compartido. Sin handoff ni modificación de estados.

## Integridad

input-receipts.json registra SHA de tres recibos ROOT, report review2 y diffs. sources-before/after.json registra 34 guardas canónicas y 36 snapshot. Tasks usa exclusivamente SHA ROOTfusion en lugar de prepare. ADR0077 y diseño detallado siguen sólo overlay. Enlaces comprobados desde destinos canónicos, overlay-links.json; no se afirma validación de anclas. inventory.json se genera al terminar, excluyéndose a sí mismo para evitar autorreferencia.

## Intento inicial conservado

attempt1/ conserva script, cases y gate NO-VERDE 16/18. DOC08 buscaba asset_role=master en vez del literal de schema asset_role:"master"; DOC12 buscaba una frase sin el sujeto intercalado. Se corrigieron únicamente esas sondas del arnés; las fuentes documentales quedaron byte-idénticas. No es un flaky de producto ni justificación de un fallo funcional.

## Salidas literales de puertas

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

```json
{"applies": true, "defined": ["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "E2E-12", "M-01", "M-02", "M-03", "M-04", "M-05", "M-06", "M-07", "M-08"], "referenced": ["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "E2E-12", "M-01", "M-02", "M-03", "M-04", "M-05", "M-06", "M-07", "M-08"], "broken_refs": 0, "tasks_sin_cobertura": [], "tests_sin_referencia": [], "gwt_cubiertos": ["CA-02", "CA-03", "CA-04", "CA-05", "CA-06", "CA-07", "CA-08", "CA-09", "CA-10", "CA-11", "CA-12", "CA-13", "CA-14", "CA-15", "CA-16", "CA-17", "CA-18", "CA-20", "CA-22", "CA-25", "CA-26", "CA-27", "CA-28", "CA-30"], "gwt_sin_cubrir": [], "gwt_sin_id": 0, "test_plan_na": false, "marcador_no_canonico": null}
```


## Aceptación ROOT — 2026-10-11T11:30:04.875828+00:00

ROOT verifica50entradas de inventario,34fuentes canónicas y36snapshot; intento1rojo16/18preservado y2verde18/18congate0. El diff del arnés modifica únicamente DOC08/DOC12: literal de roles y frase de verificación, con dos condiciones abreviadas sustituidas por literales completos más estrictos. La raíz del namespace QA se restauró al intento1 y el intento2 es independiente. Artefactos privados en `.cache/dev-cycle/m2/creative-recipes-t02-contract-qa-20261011/attempt1/` y `attempt2/`; recibo ROOT en `creative-recipes-t02-contract-review2-20261011/qa-verification-root.receipt.json`.

Se acepta el contrato documental y ADR0077; se actualizan sólo estados, fechas y frases de autoridad/publicación después de incorporar los cinco documentos revisados. El informe transcrito sustituye la ruta personal del intérprete por su ruta relativa del proyecto. T02 permanece en-progreso: Verificación propia, TDD y QA de producto pendientes. M1NO-VERDE; objetivoM0–M5activo.
