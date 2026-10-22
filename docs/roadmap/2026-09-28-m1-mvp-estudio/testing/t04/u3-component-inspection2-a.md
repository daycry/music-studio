**Lente A · U3 inspection2: 0 Critical · 0 Important · 0 Minor nuevos.** Sin defectos de requisitos o constitución identificados en la corrección de cinco archivos, contrastada con las ocho fuentes actuales de U3. **T-04 continúa abierta.**

| T-04 → criterio de aceptación | Resultado acotado a esta entrega | Evidencia `fichero:línea` |
|---|---|---|
| CA1 · Carriles, prioridad/FIFO, fechas y beats CPU | ✓ Conservados; test funcional comprueba beats CPU sin unload. | `admission.py:121`; `test_queue_references.py:141` |
| CA2 · Protocolo `EngineBackend` | ✓ Conservado; `post.audio` sigue reservado al server. | `dispatcher.py:178` |
| CA3 · Cadena N → post → N beats, semillas y referencias | ✓ Cadena atómica, índices originales, rollback y referencias al intento ganador cubiertos. | `chains.py:85`; `test_queue_chains.py:59`; `test_queue_references.py:70` |
| CA4 · Resolver por tarea verificada | ✓ Negativas conservadas; referencias nuevamente comprobadas durante la reserva. | `test_queue_chains.py:104`; `admission.py:262` |
| CA5 · Unload y VRAM libre | ✓ Flujo anterior conservado. No acredita GPU real. | `dispatcher.py:119` |
| CA6 · NDJSON, cursor, progreso y bus | ✓ Sin cambios en esta corrección; conserva evidencia U2. | `dispatcher.py:178`; `tasks.md:852` |
| CA7 · Retryable, presupuesto y offload | ✓ Política U2 conservada; el reintento manual rechaza intentos inciertos. | `manual_retry.py:109`; `test_queue_manual_retry.py:217` |
| CA8 · Recuperación, reintento manual y variantes | ✓ Corrección U3 conforme: nuevo job, request/N/seed originales y únicamente takes failed autenticados. Revalidación bajo writer. **I-01 pendiente.** | `manual_retry.py:39`, `:98`, `:187`; `test_queue_manual_retry.py:254`, `:510`, `:535` |

| Comprobación transversal | Resultado y evidencia |
|---|---|
| Tareas marcadas hechas | ✓ Ninguna se cierra: `tasks.md:171`; ocho CA siguen sin marcar, `tasks.md:183`. |
| Alcance y `Archivos` | ✓ Tres módulos de producción y dos tests corresponden a U3 y a la corrección autorizada. `tasks.md:177`; `testing/t04/dispatcher-unit-boundaries.md:11`; `scope.json`: cinco dentro, cero fuera. |
| Tests funcionales | ✓ Leídos íntegramente. Cubren fallo post propio, negativas, selección parcial, concurrencia, rollback, paginación y rechazo de caché entre sesiones/transacciones. `test_queue_manual_retry.py:361`, `:483`, `:510`; `test_queue_references.py:351`, `:399`, `:464`. |
| Constitución explícita | ✓ Sin infracción identificada de pertenencia, preservación de takes/maestro, escritura exclusiva del server, carriles o derechos. `docs/CONSTITUTION.md:10`, `:11`, `:18`, `:20`, `:43`. |
| Verificación ejecutada | ✓ Evidencia original del baseline: **506 PASS, 2 SKIP, exit 0**, argv/UTC/JUnit concordantes. **No equivale al comando exacto de cierre de `tasks.md:180`**, aún pendiente; no corresponde gap por cierre sin evidencia. |
| TDD | ✓ Cuatro RED funcionales con exit 1, JUnit y snapshots anteriores a la corrección correspondiente. Errores de fixtures/importación separados. Assertions, decoradores y parámetros históricos conservados por AST; fixture histórica corregida explícitamente en `test_queue_manual_retry.py:183`. |
| Generados y documentación E2/E3 | **No aplica interop:** el diff no toca `commands/`, `agents/` ni `hooks/`. No modifica contratos generados; conserva los límites documentados T05/I-01. |

Cobertura **completa por módulo**, de un único trace actual, cero exclusiones:

| Fuente U3 | Cobertura |
|---|---:|
| `manual_retry.py` | 92,93 % |
| `references.py` | 98,36 % |
| `admission.py` | 94,25 % |
| `dispatcher.py` | 89,63 % |
| `chains.py` | 98,80 % |

Comprobé hashes actuales/copias del baseline, JSON y datos originales de cobertura, normalizando las líneas del trace a statements con el parser de coverage. Las ocho fuentes U3 coinciden con sus sellos vigentes.

**Hallazgos anteriores:** U3-A1-01 queda resuelto por autenticación del fallo downstream y revalidación transaccional. U3-D-01 incorpora precarga local y evidencia de SELECT realmente ejecutados: **2404→11** y **132→6**; no son mediciones de latencia.

**Evidencia del revisor:** lectura estática y comprobaciones en memoria de hashes, AST, recibos y cobertura. No ejecuté suites ni escribí archivos. QA independiente, T05 real, I-01, cierre completo T-04 y Git siguen pendientes; contadores U1/U2 e inspección1 conservados.