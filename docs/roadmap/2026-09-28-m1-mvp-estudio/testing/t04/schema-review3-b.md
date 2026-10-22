**Lente B: 1 gap Important.** Revisión estática de las diez fuentes INLINE, sin herramientas ni ejecución propia.

| Criterio B | ✓/✗ | Resultado |
|---|---|---|
| Petición/opciones tipadas, identidad y reserva congelada | ✓ | Sin defectos adicionales identificados. |
| Correspondencia terminal/estado/cursor | ✓ | Validación coherente en SQL y helper. |
| R04-S01: timestamp ausente | ✓ | Corregido; se exige fecha persistida. |
| R04-B02: calendario imposible | ✓ | Corregido mediante calendario y límites horarios estrictos. |
| Compatibilidad de fechas SQL con snapshots | ✗ | Se admite un separador que el validador del snapshot rechaza. |
| Cierre, soporte, procedencia, colisiones e invalidación | ✓ | Sin otros defectos identificados. |
| Migración aditiva y fixture histórica | ✓ | Baseline conservado y ciclos actuales separados. |

| Gap | Severidad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| R04-B03 | **Important** | `apps/server/app/migrations/job_attempt_invariants.py:173` | Insertar un intento válido mediante SQL con `created_at="2026-10-07 00:00:00Z"` supera `_utc_sql`, que admite espacio como separador, y el CHECK histórico de la tabla. `validate_attempt` también lo acepta mediante `datetime.fromisoformat` (`:147`). La proyección conserva ese texto, pero `snapshots.validate` (`apps/server/app/snapshots.py:223`) aplica `FormatChecker` al formato `date-time`, que exige el separador RFC3339 `T`/`t`. La publicación falla y el snapshot no puede restaurarse pese a proceder de una fila admitida por las guardas. También afecta a `updated_at` y `deleted_at`. Es evidencia nueva de incompatibilidad SQL→snapshot; no reabre el calendario imposible ya corregido. |

**Critical: 0 · Important: 1 · Minor: 0.**

Los ✓ indican ausencia de otros defectos identificados estáticamente. Los resultados de tests y cobertura son evidencia aportada, no ejecutada por este revisor. T04 conserva sus ocho CA abiertos; esta revisión no concede aceptación técnica y QA/wheel/Docker siguen pendientes.