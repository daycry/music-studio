# QA documental independiente M3/T-01 — 2026-10-11

**VERDE documental**: 422/422 controles documentales ejecutados; 0 fallos. Gate oficial exit 0. No acredita producto M3 ni cierre del hito o de T-01.

Primer auditor NO-VERDE conservado en `diagnostic-attempt1/`: 26 falsos negativos de harness (esperaba seis celdas en tabla de cinco y contaba sólo enlaces del append, 8 frente a 14 globales). Auditor corregido; candidato y 78 pins idénticos entre ambas ejecuciones. El primer resultado no se borra ni se justifica como flaky de producto.

Candidato `dependency-contract.md` SHA `353b0df5bea112906c549acb62067b395b3ec54f07be100a81b009d8d9eeeaf1` y `iteracion-creativa.md` SHA `cbed2d35fc8036837903d0992a54afa338678d9a4852dc24293aa1906af6b698`. Corte histórico 2026-10-11T16:55:17.175557+00:00 conservado: 77 fuentes, 76 no owned, prefijo original de arquitectura 9877 bytes, 78 pins before/after. Revisión A/B precedente sin gaps es entrada; esta QA ejecutó controles propios. F77 y los cuatro payloads del documenter autenticados; sus resultados históricos no se atribuyen a esta ejecución.

Estado actual según overlay ROOT leído: M2 4/30, T04 cerrada, K1 contrato adoptado y runtime pendiente. El candidato informa M2 3/30 y T04 pendiente **en su corte histórico**, no como autoridad actual. T01 canónica en-revision; snapshot histórico en-progreso. D12 sigue propuesta: ratificación/adopción/cierre corresponden a ROOT tras QA. O1/D01 ya fijada; ADR0037 permite sólo componentes independientes autorizados. Fuente/fact/lector/versión/autoridad/gate comprobados en las 25 filas, referencias F resueltas, readers AST contrastados sin importar ni ejecutar runtime.

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 422,
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

25 seams, 77 SHA históricos, 14 enlaces relativos comprobados desde el destino canónico y seis tablas. Para el enlace al candidato aún ausente se usa SOURCECUT privado declarado; referencias privadas F62–F66 se autentican en el snapshot histórico. Ninguna ruta `.cache` se interpreta como enlace público, CI o evidencia viva de autorización.

| Control individual | Resultado |
|---|---|
| Inventario F1-F77 completo | PASS |
| 25 seams exactos S01-S25 | PASS |
| Seam S01 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S02 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S03 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S04 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S05 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S06 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S07 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S08 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S09 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S10 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S11 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S12 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S13 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S14 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S15 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S16 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S17 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S18 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S19 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S20 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S21 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S22 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S23 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S24 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seam S25 fuente/autoridad/formato/reader/disponibilidad/gate/consumidor | PASS |
| Seis tablas Markdown | PASS |
| Enlace docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md -> tasks.md | PASS |
| Enlace docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md -> ../../decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md | PASS |
| Enlace docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md -> ../../decisiones/ADR-0037-avance-tecnico-condicionado.md | PASS |
| Enlace docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md -> improvement-plan.md | PASS |
| Enlace docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md -> test-plan.md | PASS |
| Enlace docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md -> ../../legal/licencias.md | PASS |
| Enlace docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md -> test-plan.md | PASS |
| Enlace docs/arquitectura/iteracion-creativa.md -> ../roadmap/2026-10-10-m2-iteracion-creativa/recipe-contract-design.md | PASS |
| Enlace docs/arquitectura/iteracion-creativa.md -> ../decisiones/ADR-0077-envelope-privado-de-recetas-creativas.md | PASS |
| Enlace docs/arquitectura/iteracion-creativa.md -> ../decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md | PASS |
| Enlace docs/arquitectura/iteracion-creativa.md -> ../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md | PASS |
| Enlace docs/arquitectura/iteracion-creativa.md -> ../roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md | PASS |
| Enlace docs/arquitectura/iteracion-creativa.md -> ../decisiones/ADR-0079-composicion-creativa-por-muestras-medidas.md | PASS |
| Enlace docs/arquitectura/iteracion-creativa.md -> ../roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md | PASS |
| 14 enlaces relativos | PASS |
| Nueve bloqueos explícitos | PASS |
| D12 propuesta y ROOT posterior | PASS |
| O1 y ADR0037 avance condicionado | PASS |
| Hash y lock no autoridad | PASS |
| Receipt2 distinto Manifest2 | PASS |
| CA01 sin cierre anticipado | PASS |
| CA48 CPU sin engine/model/seed fake | PASS |
| Versiones y bytes históricos | PASS |
| Codefirst DTO y migraciones delimitadas | PASS |
| Privado no falsa CI | PASS |
| Ninguna función M3 implementada | PASS |
| Overlay actual ROOT separado del corte | PASS |
| Reader AST F41 inspect_journal | PASS |
| Reader AST F41 decide_request | PASS |
| Reader AST F42 read_handle_geometry | PASS |
| Reader AST F29 read_recipe | PASS |
| Reader AST F29 read_request | PASS |
| Reader AST F30 read_composition_plan | PASS |
| Reader AST F36 project | PASS |
| Reader AST F36 validate | PASS |
| Reader AST F36 restore | PASS |
| Reader AST F50 verify_private_context | PASS |
| Reader AST F51 verify_manifest | PASS |
| Proof documenter docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md | PASS |
| Proof documenter docs/arquitectura/iteracion-creativa.md | PASS |
| Proof documenter documenter-verification.receipt.json | PASS |
| Proof documenter documenter-verification.stdout | PASS |
| F77 ADR0081 conservado | PASS |
| Recibo histórico legible F62 | PASS |
| Recibo histórico legible F63 | PASS |
| Recibo histórico legible F64 | PASS |
| Arquitectura prefijo intacto y append seul | PASS |
| T01 canónica en-revision; histórica en-progreso | PASS |
| Oficial ledger exit0 | PASS |
| Oficial coverage exit0 | PASS |
| Oficial knowledge exit0 | PASS |

La lista completa nombrada de controles, resultados, detalles y horas UTC está en el namespace privado `.cache/dev-cycle/m3/dependency-contract-t01-current-qa1-20261011/raw/controls.json`. Evidencia raw: `results.json`, `qa-gate.stdout`, `qa-gate.receipt.json`, `ledger.stdout`, `coverage.stdout`, `knowledge.stdout`, `before.json`, `after.json`, `links.json` y recibos argv/cwd/UTC/exits/reaped/source/tool SHA. El manifest privado fija SHA de todos los payloads y la ruta real de este informe canónico; se excluye a sí mismo.

TDD/cobertura n/a prosa: `coverage-check` mide trazabilidad del plan, no porcentaje runtime. No E2E/browser, HTTP, GPU, Docker, nativo, SQLite, instalación, servicios, herramientas/modelos de producción ni funcionalidades M3 ejecutados. Guardrail local/privado respetado: no hubo host objetivo ni acceso de red. PDF opcional omitido porque este alcance documental no añade verificación visual. Consumo real tokens/euros/horas IA null; UTC de pared no equivale a trabajo IA medido.

Pendientes para producto: todos los E2E y M del test-plan permanecen sin ejecutar. En particular M-01/CA-01 requiere cierre M2 y acta ROOT independiente; M-48/CA-48 requiere inspección instrumental de provenance/rights/históricos mixtos. Nueve bloqueos permanecen; hash/lock no autoridad, receipt2 distinto Manifest2, sin engine/seed/winningattempt ficticio CPU, sin cierre anticipado M1/M2/M3. No se modifica ledger, contrato candidato ni otras fuentes canónicas; único archivo canónico nuevo es este informe. ROOT ratificará D12 y decidirá adopción/cierre de T01.
