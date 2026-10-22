**Lente B · M1/T-02 · intento 4: ✓ — sin defectos en el alcance reevaluado.**

Revisión estática exclusivamente del material INLINE. No ejecuté herramientas, pruebas ni comprobaciones de hashes.

| Criterio | ✓/✗ | Evidencia y valoración |
|---|:---:|---|
| R02-12: impedir promoción ordinaria de soporte | ✓ | `apps/server/app/migrations/fix3_invariants.py:6`: rechaza el cambio de marca sin excepción de importación y toda degradación de proyecto completo. También cubre promoción y edición combinadas en un UPDATE. |
| Conservar promoción validada compatible | ✓ | `apps/server/app/snapshots.py:584`: comprueba colisiones antes de abrir `snapshot_import`; la promoción ocurre dentro de esa transacción y la excepción se elimina antes del commit (`:624`). |
| R02-18: reutilizar lecturas sin carrera | ✓ | `apps/server/app/snapshots.py:560`: adquiere el escritor antes de consultar colisiones. Las consultas por lotes de hasta 400 (`:575`) y la reutilización (`:600`) comparten conexión y transacción. |
| Rollback y validación final | ✓ | `apps/server/app/snapshots.py:556`: colisiones, inserciones y comprobación final de raíces (`:616`) quedan dentro de la misma transacción; un fallo revierte también la promoción y la excepción. |
| Defectos nuevos introducidos por fix3 | ✓ | No identifico un escenario concreto de fallo nuevo en el delta suministrado. |

**Critical: 0 · Important: 0 · Minor: 0.**

R02-12 y R02-18 muestran corrección suficiente desde esta lente. Los escenarios previamente aprobados conservan su valoración. La adjudicación de IDs corresponde a raíz; este resultado no acredita QA, cierre de T-02, M-03, Git ni aceptación humana.