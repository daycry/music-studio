# T-18 — Revisión adversarial, intento 2

Se conservan los aprobados de [revisión 1](review-attempt1.md) y se reevalúan A1/B1/B2 y sus aristas nuevas. La herramienta impidió crear agentes nuevos por límite de threads; se reutilizan contextos de los revisores anteriores, que no observaron la implementación del fix. Esta degradación se declara y no se presenta como dos contextos nuevos. Scope exit 0, sin avisos ni archivos fuera de alcance; selector C/D=false. Journals ajenos preservados.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| A1: key compatible con el schema anterior | ✓ corregido | Descriptor conserva string; tests de longitudes 0/33 pasan para canción e instrumental |
| B1: semilla base resuelta e índice exacto | ✓ corregido | Manifest verifica base más índice; tests de dos variantes con semilla explícita/nula, manipulación dentro/fuera del rango e índices inválidos |
| B1: petición de origen intacta | ✓ | El binding no cambia original/effective.seed=None; prueba ejecutada |
| B2: hash declarado cruzado con bytes fuente | ✓ corregido | Rechazo en preparador y verificador; BOM/CRLF probado separadamente del texto efectivo |
| Ejecución de recibo malformada | ✓ | B ejecuta nueve casos rechazados por ambos verificadores; referencia sin ejecución rechazada |
| Contratos y documentación | ✓ | Índice opcional en schema; cuatro manifiestos legados válidos, exportador al día; ADR/pipeline/procedencia actualizados |
| Original/efectivo, tags, offline, autoría, privacidad y publicación | ✓ conservado | Sin evidencia nueva contra aprobaciones anteriores; suite completa del alcance verde |
| Revisión y QA para cierre | Pendiente QA | T-18 permanece en revisión; no se afirma cierre por la revisión |

A ejecutó siete regresiones, exportador y cuatro ejemplos; B ejecutó los seis módulos declarados: **185 passed, 1 skipped, cinco warnings existentes**, exit 0, más los nueve casos de ejecución malformada. Cobertura cambiada leída del recibo: mínimo 88,14 %, sin recalcularla. No se modificó producción, ledger ni informes por los revisores.

Fusión: A1/B1/B2 corregidos, cero Critical/Important/Minor pendientes, sin rebates. Contextos de revisión reutilizados por la limitación descrita; independencia respecto a implementación conservada. Ventana cerrada antes de QA, consumo estimado con horas/tokens/coste reales desconocidos. No se declara calidad musical ni cierre de M0.
