# Informe QA — M1/T-05 (modo sin UI, acotado)

Estado: **NO VERDE para el gate** (sin evidencia E2E) — ℹ️ no es un fallo de T-05.

- Alcance: T-05 backend. Ninguna E2E-xx la cubre aún (batería = T-15). No se lanzó Playwright ni se levantó el stack. Guardrail: sin ejecución contra URL.
- `ledger-lint`: 0 incoherencias · 32 avisos (criterios de aceptación y Changelog ausentes en tareas distintas de T-05... ver ledger).
- `coverage-check`: broken_refs 0; `referenced: []`; las 17 tareas (incl. T-05) y los 16 tests figuran sin cobertura declarada (el test-plan usa su propia tabla de trazabilidad —T-05 → E2E-01, E2E-09, M-01— que el script no reconoce como «Cubre (tests)»); gwt_sin_cubrir: [].
- `qa-gate.py testing/raw/results.json`: `{"verdict":"NO-VERDE","reason":"sin resultados: results.json no existe (la ausencia de evidencia es rojo)"}` — exit 1.
- Pendiente: M-01 (aceptación final en T-16, cobertura compartida T-04/T-05).
- Sin handoff a documenter ni cambio de estados.
