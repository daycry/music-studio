# Informe de QA — contrato durable CPU M2/T-05

| Campo | Resultado |
|---|---|
| Fecha | 2026-10-11 UTC |
| Estado del componente | VERDE documental, qa-gate exit 0; 34/34 controles |
| Estado del producto | ABIERTO; T-05/T-07/M2 no completados |
| URL auditada | No aplica: auditoría de prosa sin app ni E2E |
| Plan | [Plan](../improvement-plan.md) · [Test-plan](../test-plan.md) |
| Fuente | creative-persistence-contract.md privado, 97459 bytes, 461 líneas |
| SHA-256 | `a608b81f44081a7065fcf4556dfb0c27ea1234c485981ee9c70e729eedce7e6b` |

## Veredicto (qa-gate documental)

El marcador de alcance en results.json es `PROSA-component`. El runner propio de biblioteca estándar adapta sus comprobaciones al esquema leído por qa-gate; no es una ejecución Playwright. Cada resultado enlaza un control de checks.json y el auditor audit.py. El JSON siguiente sólo decide este componente documental.

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 34,
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

Exclusiones explícitas: runtime, SQL/ORM/DB y migraciones ejecutadas, API ejecutada, FFmpeg/audio/render, GPU/Docker/WSL, UI/E2E y manuales de producto. No se obtuvo ningún resultado sobre esas capas. TDD n/a: prosa. Cobertura de código n/a; no se ejecuta cobertura unit-test sobre una implementación futura. No se usa `test-plan: n/a (sin UI)` para eximir el plan M2, que sí contiene UI.

## Resumen y límites

Se autentican 120 fuentes del snapshot, 119 guards canónicos y una ausencia, antes y después del auditor. Los dos apéndices son extracción byte exacta de la fuente y los candidatos conservan los prefijos canónicos exactos; source.diff se reconstruye sobre los bytes actuales, incluido el original sin newline final de iteracion-creativa. La diferencia de tasks.md prepare→release está declarada por ROOT en context_drifts y coincide exactamente; no hay otro drift autorizado.

La comprobación independiente contrasta AST de Take.batch_id (Mapped[str]/String(26), sin FK/Batch), DDL externo 0001_schema.sql NOT NULL/CHECK/índice, source_sha256 NOT NULL de 0006, import/llamada dinámicos install y uso actual Base.metadata. Esa última dependencia confirma que freeze legacy todavía es trabajo de implementación; la prosa exige aislarla y no prueba que esté corregida en runtime. Copias Song v1 son idénticas. Las 26 entradas normativas SQL/ORM/READ/MIG/BACK/DOWN/API/PORT/PREV se auditan como obligaciones, no como tests ejecutados.

Reserva PRE-render y PUB final tienen fronteras coherentes: reserva propia sin IDs finales ni source/receipt; receipt real y cierre propio antes de reservePUB; grupo ULID derivado de reserva, CAS conjunto execution/hash/batch sólo antes de ready e historia por ordinal preservada. FK diferidas más guardas recíprocas cubren grafo completo sin atribuir triggers de commit a SQLite. Los hashes tienen dominios propios y una coincidencia source/padre no acredita ejecución. API conserva cuatro paths aditivos, ownership antes de 409 y rechazo antes de writes. Preview no fabrica Take/asset/PUB; import inicializa UNKNOWN y T-07 conserva reconciliación/executor/publicador reales.

Las tablas 32A/11B y los tres gaps previos se conservan en los traspasos autenticados. A01=B01, A02 y B02 están corregidos documentalmente; no aparecen gaps documentales nuevos. La adopción pertenece a ROOT.

## Puertas y trazabilidad

ledger-lint exit 0: **0 incoherencias, 29 avisos**. Incluye 27 avisos de Changelog ausente y dos cabeceras de revisión no reconocidas (líneas 1336 y 1346); no se modifica el ledger. coverage-check exit 0 sólo verifica trazabilidad declarada: cero referencias rotas, cero tareas sin cobertura, cero tests sin referencia y cero GWT sin cubrir. No acredita ejecución E2E.

```json
{"applies": true, "defined": ["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "E2E-12", "M-01", "M-02", "M-03", "M-04", "M-05", "M-06", "M-07", "M-08"], "referenced": ["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "E2E-12", "M-01", "M-02", "M-03", "M-04", "M-05", "M-06", "M-07", "M-08"], "broken_refs": 0, "tasks_sin_cobertura": [], "tests_sin_referencia": [], "gwt_cubiertos": ["CA-02", "CA-03", "CA-04", "CA-05", "CA-06", "CA-07", "CA-08", "CA-09", "CA-10", "CA-11", "CA-12", "CA-13", "CA-14", "CA-15", "CA-16", "CA-17", "CA-18", "CA-20", "CA-22", "CA-25", "CA-26", "CA-27", "CA-28", "CA-30"], "gwt_sin_cubrir": [], "gwt_sin_id": 0, "test_plan_na": false, "marcador_no_canonico": null}
```

| Tarea | Evidencia actual | Estado |
|---|---|---|
| T-05 | Contrato privado/AST/baseline/apéndices/hashes; 34 controles propios | Conforme documental; implementación y verificación reales pendientes |
| T-07 | Contrato separa capacidad y recibo real del codec | Executor/publicador/reconciliación/serving pendientes |
| M2 global | E2E-01–12 y M-01–08 sólo trazados | Abierto; no qa-gate global de producto |

## Resultados automáticos documentales

| Control | Resultado |
|---|---|
| AUTH-SNAPSHOT | PASA |
| AUTH-CANON | PASA |
| SOURCE-EXACT | PASA |
| RELEASE-PREPARE | PASA |
| APPENDIX-DATOS | PASA |
| CANDIDATE-DATOS | PASA |
| APPENDIX-ITERACION | PASA |
| CANDIDATE-ITERACION | PASA |
| DIFF-SCOPE | PASA |
| DIFF-APPENDIX-datos | PASA |
| DIFF-APPENDIX-iteracion-creativa | PASA |
| DIFF-CONTRACT-BYTES | PASA |
| CODEC-CLOSED | PASA |
| HASH-DOMAINS | PASA |
| PRE-RENDER-GRAPH | PASA |
| BATCH-CAS-HISTORY | PASA |
| FINAL-PUB-AUTHORITY | PASA |
| GUARDS-SYMMETRIC | PASA |
| MIGRATION-BOUNDARY | PASA |
| SNAPSHOT-HISTORY | PASA |
| API-OWNERSHIP | PASA |
| PREVIEW-NO-CONTENT | PASA |
| T07-NO-FALSE-AUTHORITY | PASA |
| AST-TAKE-BATCH | PASA |
| AST-BASELINE-BATCH | PASA |
| AST-0006-DYNAMIC-INSTALL | PASA |
| AST-0006-SOURCE-NOTNULL | PASA |
| AST-FREEZE-OBLIGATION | PASA |
| AST-NO-RECIPE-BATCH-recipes | PASA |
| AST-NO-RECIPE-BATCH-composition | PASA |
| SONGV1-COPIES | PASA |
| MATRIX-IDENTITIES | PASA |
| REVIEW-HISTORY | PASA |
| LEDGER-CONSISTENCY | PASA |

Detalles y líneas exactas: `evidence/checks.json`. Primera pasada preservada en `evidence/attempt1/`: 27/34, siete diagnósticos del auditor. Se corrigieron el manejo del drift declarado, reconstrucción del diff sin newline, tres literales, localización del DDL externo y conteo de 26 IDs. Ninguna fuente candidata fue modificada; el gate final corresponde al SHA final del auditor. El error de quoting de una orden PowerShell y la lectura cp1252 diagnóstica no ejecutaron mutación de fuentes; no son fallos del producto.

## Checklist manual pendiente

- [ ] **M-01 — Edición y fidelidad real de las uniones**: pendiente de QA de producto conforme al test-plan.
- [ ] **M-02 — Igualación A/B, decoder y transporte real**: pendiente de QA de producto conforme al test-plan.
- [ ] **M-03 — Cuatro capacidades musicales y 30 generaciones propias**: pendiente de QA de producto conforme al test-plan.
- [ ] **M-04 — LLM elegido y Ollama compartido real**: pendiente de QA de producto conforme al test-plan.
- [ ] **M-05 — Custodia, manifiestos y replay persistente real**: pendiente de QA de producto conforme al test-plan.
- [ ] **M-06 — Provider opcional: revisión de privacidad y coste**: pendiente de QA de producto conforme al test-plan.
- [ ] **M-07 — Teclado, castellano, foco y utilidad**: pendiente de QA de producto conforme al test-plan.
- [ ] **M-08 — Puertas de calidad, compatibilidad y cierre**: pendiente de QA de producto conforme al test-plan.

## Evidencias y PDF

Evidencia propia: `.cache/dev-cycle/m2/creative-persistence-t05-contract-current-qa1-20261011/evidence/`. Incluye audit.py, checks.json, results.json, audit.receipt.json, authentication-before.json, authentication-after-audit.json, command-receipts.json y salidas originales de los tres gates. Recibos de comandos contienen argv, UTC, exit y SHA de script/stdout/stderr. Uso medido tokens/euros/horas IA: null; no se inventan medidas.

PDF propio `evidence/report.pdf`, generado por la tubería to-pdf con Node, dependencias y Chromium ya instalados dentro del repositorio; sin descargas ni perfiles ajenos. El recibo de render registra el resultado real. No se certifica inspección visual de páginas PDF rasterizadas: esa revisión no se ha realizado. No hay capturas E2E porque no se abrió una app. Guards finales y payload hashes se entregan en qa.receipt.json.

Sin cambios de código, ledger, CAS, Git, estado de plan/spec ni publicación externa. ROOT puede incorporar el contrato después de autenticar esta evidencia. No procede handoff documenter ni cierre de T-05 por este verde documental.
