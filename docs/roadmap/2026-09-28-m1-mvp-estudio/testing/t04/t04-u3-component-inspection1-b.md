**0 Critical · 1 Important · 0 Minor.**

| Criterio | Resultado | Evidencia / escenario concreto |
|---|---|---|
| Cadena atómica, variantes y rollback | ✓ | `chains.py:173`; sin defectos adicionales identificados. |
| Referencias y reserva con validación actual | ✓ | `references.py:73`, `admission.py:301`; sin defectos adicionales identificados. |
| Reintento tras fallo de post-proceso | ✗ Important | [manual_retry.py:44](../../../../../apps/server/app/queue/manual_retry.py:44): si la generación termina con `done` durable y después falla `post.audio`, las tomas pueden estar `failed` mientras el job generador permanece `succeeded`. El servicio rechaza ese generador con `Owned failed generation required`. Pasar el job de post-proceso tampoco funciona: `validate_request` exige una tarea musical y la selección busca takes vinculados al job original. El reintento queda bloqueado. |
| Concurrencia, rollback y protección de ACK incierto | ✓ | `manual_retry.py:58`, `manual_retry.py:118`; sin defectos adicionales identificados. |

El test `test_queue_manual_retry_historical_attempt_and_extra_outputs_not_ready_assets` oculta el defecto: su helper `failed()` cambia artificialmente también el generador a `failed`.

**Evidencia:** análisis estático y sonda en memoria de `_selection` real, con `live_song` sustituido; reprodujo el rechazo de un generador `succeeded`. No ejecuté integración SQLite ni suites. Los ocho hashes coinciden con el freeze; los artefactos actuales muestran 471 PASS, 2 SKIP y cobertura completa por cada uno de los cinco módulos ≥80 %, sin exclusiones. T05 real permanece pendiente.