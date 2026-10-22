# QA documental independiente — contrato store M1/T05

**VERDE documental**. 95/95 comprobaciones reales. No aceptación T05/M1.

## Alcance y fuentes

Snapshot readonly de 21 fuentes; 19 guards canónicos. El release/fusión y ambas respuestas de review2 están fijados por SHA. Diseño seleccionado O2; ADR propuesta, adopción e implementación no liberadas. Seis ocurrencias corregidas y tres aristas de integración resueltas sólo en snapshot, con destino/hash en `raw/document-checks.json`; las dos aristas repetidas no se cuentan como destinos únicos. No se auditó todo el grafo global de spec/plan.

Constitución §2: todo dentro del proyecto y sólo server escribe SQLite. No se abrió BD, producción, GPU, Ollama, servicio, admin o experimento nativo. Ledger leído desde bytes UTF8 con replacement explícito para el byte histórico inválido; no reescrito.

## Gate oficial — adaptación transparente

`raw/results.json` adapta los outcomes reales de `qa_harness.py` al esquema de suites admitido por qa-gate.py. No es reporter Playwright, JUnit, E2E ni cobertura. E2E/unit/coverage-check: n/a al alcance documental, no ejecutados; no exención global de M1.

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 95,
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

## Resultados

| ID | Resultado | Comprobación |
|---|---|---|
| DOC-001 | PASS | snapshot SHA docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md |
| DOC-002 | PASS | snapshot SHA docs/decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md |
| DOC-003 | PASS | snapshot SHA docs/CONSTITUTION.md |
| DOC-004 | PASS | snapshot SHA docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md |
| DOC-005 | PASS | snapshot SHA scripts/storage_journal_windows.py |
| DOC-006 | PASS | snapshot SHA packages/storage-guard/studio_storage_guard/receipt.py |
| DOC-007 | PASS | snapshot SHA .claude/dev.json |
| DOC-008 | PASS | snapshot SHA tests/test_storage_journal.py |
| DOC-009 | PASS | snapshot SHA docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md |
| DOC-010 | PASS | snapshot SHA AGENTS.md |
| DOC-011 | PASS | snapshot SHA docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md |
| DOC-012 | PASS | snapshot SHA docs/decisiones/ADR-0076-politica-estricta-de-confianza-del-journal-windows.md |
| DOC-013 | PASS | snapshot SHA docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-nt-geometry-current-qa1-2026-10-11.md |
| DOC-014 | PASS | snapshot SHA docs/decisiones/README.md |
| DOC-015 | PASS | snapshot SHA docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md |
| DOC-016 | PASS | snapshot SHA docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md |
| DOC-017 | PASS | snapshot SHA tests/test_storage_journal_windows.py |
| DOC-018 | PASS | snapshot SHA docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md |
| DOC-019 | PASS | snapshot SHA docs/decisiones/ADR-0078-geometria-nt-readonly-del-journal.md |
| DOC-020 | PASS | snapshot SHA docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md |
| DOC-021 | PASS | snapshot SHA scripts/storage_journal.py |
| DOC-022 | PASS | canonical SHA docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md |
| DOC-023 | PASS | canonical SHA docs/decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md |
| DOC-024 | PASS | canonical SHA docs/CONSTITUTION.md |
| DOC-025 | PASS | canonical SHA docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md |
| DOC-026 | PASS | canonical SHA scripts/storage_journal_windows.py |
| DOC-027 | PASS | canonical SHA packages/storage-guard/studio_storage_guard/receipt.py |
| DOC-028 | PASS | canonical SHA .claude/dev.json |
| DOC-029 | PASS | canonical SHA tests/test_storage_journal.py |
| DOC-030 | PASS | canonical SHA docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md |
| DOC-031 | PASS | canonical SHA AGENTS.md |
| DOC-032 | PASS | canonical SHA docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md |
| DOC-033 | PASS | canonical SHA docs/decisiones/ADR-0076-politica-estricta-de-confianza-del-journal-windows.md |
| DOC-034 | PASS | canonical SHA docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-nt-geometry-current-qa1-2026-10-11.md |
| DOC-035 | PASS | canonical SHA docs/decisiones/README.md |
| DOC-036 | PASS | canonical SHA docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md |
| DOC-037 | PASS | canonical SHA docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md |
| DOC-038 | PASS | canonical SHA tests/test_storage_journal_windows.py |
| DOC-039 | PASS | canonical SHA docs/decisiones/ADR-0078-geometria-nt-readonly-del-journal.md |
| DOC-040 | PASS | canonical SHA scripts/storage_journal.py |
| DOC-041 | PASS | review a pin |
| DOC-042 | PASS | review b pin |
| DOC-043 | PASS | fusion release byte exact |
| DOC-044 | PASS | diff original pin |
| DOC-045 | PASS | diff scope four documents |
| DOC-046 | PASS | design frontmatter release boundaries |
| DOC-047 | PASS | ADR proposal and boundaries |
| DOC-048 | PASS | link occurrence 1 |
| DOC-049 | PASS | link occurrence 2 |
| DOC-050 | PASS | link occurrence 3 |
| DOC-051 | PASS | link occurrence 4 |
| DOC-052 | PASS | link occurrence 5 |
| DOC-053 | PASS | link occurrence 6 |
| DOC-054 | PASS | link occurrence 7 |
| DOC-055 | PASS | link occurrence 8 |
| DOC-056 | PASS | link occurrence 9 |
| DOC-057 | PASS | J01 invariant and causal test |
| DOC-058 | PASS | J02 invariant and causal test |
| DOC-059 | PASS | J03 invariant and causal test |
| DOC-060 | PASS | J04 invariant and causal test |
| DOC-061 | PASS | J05 invariant and causal test |
| DOC-062 | PASS | J06 invariant and causal test |
| DOC-063 | PASS | J07 invariant and causal test |
| DOC-064 | PASS | J08 invariant and causal test |
| DOC-065 | PASS | J09 invariant and causal test |
| DOC-066 | PASS | J10 invariant and causal test |
| DOC-067 | PASS | C0 cutpoint defined once |
| DOC-068 | PASS | C1 cutpoint defined once |
| DOC-069 | PASS | C2 cutpoint defined once |
| DOC-070 | PASS | C3 cutpoint defined once |
| DOC-071 | PASS | C4 cutpoint defined once |
| DOC-072 | PASS | C5 cutpoint defined once |
| DOC-073 | PASS | C6 cutpoint defined once |
| DOC-074 | PASS | C7 cutpoint defined once |
| DOC-075 | PASS | O2/S1/G2 kept |
| DOC-076 | PASS | nominal capabilities/token not authority |
| DOC-077 | PASS | trust fullchain and no adoption |
| DOC-078 | PASS | kernel access and native flush gate |
| DOC-079 | PASS | aligned arena ownership |
| DOC-080 | PASS | CAS/replay/ACK ordered |
| DOC-081 | PASS | poison custodia no retry |
| DOC-082 | PASS | recovery blocked causal pending |
| DOC-083 | PASS | probe never full chain |
| DOC-084 | PASS | bootstrap/ext4/manual/product not accepted |
| DOC-085 | PASS | readonly legacy seams |
| DOC-086 | PASS | readonly canonical fallback signature ReceiptLease |
| DOC-087 | PASS | readonly canonical fallback signature PublishedDiskBinding |
| DOC-088 | PASS | constitution server only and local |
| DOC-089 | PASS | T05 open and three unchecked acceptance |
| DOC-090 | PASS | spec approved not implemented |
| DOC-091 | PASS | plan not completed |
| DOC-092 | PASS | official ledger lint |
| DOC-093 | PASS | additional seam sources unchanged |
| DOC-094 | PASS | all before after sources byte exact |
| DOC-095 | PASS | tools unchanged |

## Evidencia y trazabilidad

[Checks y líneas](raw/document-checks.json), [antes](raw/sources-before.json), [después](raw/sources-after.json), [tools](raw/tool-pins.json), [procesos/argv/UTC/streams/exits/reaps](raw/processes.json), [gate stdout](raw/qa-gate.stdout), [ledger stdout](raw/ledger.stdout). T05 sigue en-progreso con tres criterios sin marcar. Spec aprobada y plan borrador permanecen abiertos; ninguna fuente/ledger canónicos modificados.

## Límites y manuales pendientes

- [ ] Testigo nativo WRITE_DATA sin APPEND_DATA con FlushFileBuffers sobre mismo access/mode.
- [ ] Cadena S1 positiva provisionada y G2 actual writable; leaf 8f0 readonly no confiere autoridad.
- [ ] Bootstrap físico/legacy, lifecycle, correlación de recovery causal y powerloss/reinicio.
- [ ] Ext4/UUID reales, E2E de producto y escucha/backup/restauración manuales del plan M1.

Estas comprobaciones acreditan coherencia documental y preservación de contratos, no ejecución de CAS/ACK/kernel. J01–J10 y C0–C7 son requisitos futuros; su presencia y contenido se contrastaron, no sus pruebas nativas. No PDF: opcional y omitido, sin instalación ni rasterizado. No captura de UI: no UI ejecutada.

Entrega DONE_WITH_CONCERNS por límites de evidencia de producto expresamente pendientes; sin gap documental detectado si gate verde. ROOT verifica/adopta; QA no cierra estados. `payload-manifest.json` excluye sólo su propio fichero para evitar autorreferencia; snapshot y todos los payloads regulares restantes incluidos, sin cache disposable creada.

Diagnóstico attempt1 preservado íntegro en `diagnostic-attempt1/`: 91/92 PASS, fallo de selector DOC-083 que buscaba texto del ADR en el diseño. Selector corregido a frase equivalente del diseño; criterio sin cambios. Patch inicial de harness rechazado atómicamente por contexto, sin cambio parcial. Dos firmas readonly consultadas por fallback canónico, hashes before/after en `raw/seam-sources.json`; no se agregan al conteo snapshot21.

Sello final: [launcher managed uv/argv/UTC/PID/exit0/reaped](raw/launcher.receipt.json), [stdout real](raw/harness.stdout), [stderr real](raw/harness.stderr), [guards finales](final-seal.receipt.json). El manifiesto se regeneró después de cerrar stdout y recibir el exit del launcher; evita hashes de streams todavía abiertos.


## Verificación y adopción ROOT

Revisión2A/B0gaps yQA documental95/95,gateverde; ROOTverifica60payload/21fuentes/19guardascanónicas/2seams/7tools. ContratoO2incorporado, sin implementación ni evidencia nativeFlush/ACK/fullchainS1/bootstrap/lifecycle/causalrecovery/ext4/E2E/manuales. Esos gates siguen obligatorios. Implementación futura sólo por unidad liberada yTDD/revisión/QA; no cierreT05/M1. Originales privados íntegros.

Informeoriginal yrecibos privados en `.cache/dev-cycle/m1/storage-journal-store-contract-current-qa1-20261011`; manifiesto60payload verified. PDFopcionalomitido, no raster/preview declarado.
