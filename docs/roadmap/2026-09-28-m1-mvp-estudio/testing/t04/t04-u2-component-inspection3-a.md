**Lente A · T-04/U2 · inspección 3: 0 Critical / 1 Important / 0 Minor.** Dictamen limitado al delta del componente; no acepta U2, U3 ni T-04 completa.

| T-04 → criterio de aceptación | Resultado | Evidencia fichero:línea |
|---|---|---|
| GPU1/CPU2, prioridad/FIFO, `not_before`, CPU sin unload GPU | ✗ Nuevo fallo de paginación compartida, A3-01. El orden entre poblaciones sí está corregido | `runtime.py:342`; `admission.py:199`; `test_dispatcher_retry.py:992`, `:1619` |
| Protocolo `EngineBackend` | ✓ Conservado en el delta | `dispatcher.py:7`; `runtime.py:190`, `:506` |
| Cadena generación → post → beats | Pendiente, correctamente abierta | `tasks.md:185`; fuera de U2 |
| Resolver por tarea verificada | ✓ Validación positiva fresca conservada | `runtime.py:481`; `dispatcher.py:183`; `test_dispatcher_retry.py:61` |
| Unload y comprobación de VRAM | ✓ Sin defecto adicional identificado | `dispatcher.py:128`; `runtime.py:277`; `test_dispatcher_retry.py:527` |
| NDJSON, reenganche y bus | ✓ Conservado; aceptación general pendiente | `runtime.py:213`; `tasks.md:188` |
| Retry durable, máximo dos y offload una vez | ✓ Autoridad de reserva conservada | `retry.py:32`, `:155`; `test_dispatcher_retry.py:770` |
| Recuperación con mismo ID/payload | ✓ Conservada; manual, continuación CPU y batch/serie pendientes | `runtime.py:190`; `tasks.md:190` |

**A3-01 · Important — El selector queued invalida el cursor ORM de retries.**

Ubicación: [admission.py:199](../../../../../apps/server/app/queue/admission.py:199), [runtime.py:344](../../../../../apps/server/app/queue/runtime.py:344), [retry.py:122](../../../../../apps/server/app/queue/retry.py:122). Requisito: [tasks.md:183](../../../../../docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:183), prioridad/FIFO y despacho de candidatos elegibles.

Escenario: más de 400 retries y más de 400 jobs queued cuyos órdenes se intercalan. Ambos lectores comparten Session. Al avanzar otra página queued, `expunge_all()` sustituye su identity map mientras el resultado streaming de retries todavía conserva el anterior. Al materializar la siguiente partición de retries, SQLAlchemy lanza `InvalidRequestError: … identity map is no longer valid`. `_run()` no captura esa excepción (`runtime.py:534`), por lo que el dispatcher termina y deja candidatos pendientes.

**Prueba propia ejecutada:** SQLite exclusivamente en memoria, cursor ORM `yield_per=400`, 801 filas y `expunge_all()` entre particiones; reprodujo ese `InvalidRequestError`. Es prueba del mecanismo SQLAlchemy, no una reproducción del runtime completo. La conexión al flujo productivo procede de lectura estática. Los tests actuales no cubren la renovación intercalada: `test_dispatcher_retry.py:1473` combina 801 retries con un queued; `:1372` crea los retries antes de los queued.

| Comprobación transversal | Resultado |
|---|---|
| Tareas hechas y Verificación contractual | ✓ T-04 sigue `en-progreso` con ocho CA abiertos (`tasks.md:171`, `:183`). No detecto cierre sin evidencia; no ejecuté su Verificación para suplirla. |
| Alcance y `Archivos` | ✓ Los cinco archivos modificados corresponden a cola y tests previstos (`tasks.md:177`). Scope: cinco dentro, cero fuera, cero excluidos; `.claude/dev.json` no añade exclusiones. |
| Tests y cobertura actual | ✓ Traza original normalizada contra fuentes actuales: runtime **91,06 %**, retry **94,23 %**, dispatcher **90,00 %**, admission **94,63 %**; cada módulo completo supera 80 %, cero exclusiones. Esto no cubre A3-01. |
| TDD del delta | ✓ Ambos RED preceden a producción: fuentes archivadas coinciden con preimágenes; argv/UTC/exit/JUnit originales presentes. Prioridad: 2 FAIL/2 PASS; lector: 1 FAIL por `ValueError`, no por colección/importación. |
| Cancelación del lector | ✓ Corrección anterior comprobada por lectura y evidencia entregada: espera al futuro nativo real antes del cierre, conserva la causa y protege shutdown (`runtime.py:54`, `:81`, `:541`; tests `:1092`, `:1510`). |
| Constitución | ✓ Sin nueva violación explícita identificada: server escritor, residencia y cierre con Verificación (`docs/CONSTITUTION.md:18`, `:21`, `:33`). |
| Generados/descripciones E2/E3 | No aplica al exportador interop: el diff no toca `commands/`, `agents/` ni `hooks/`. Sin cambio de contrato que requiera regeneración identificado. |
| Custodia | ✓ Cinco fuentes cambiadas y siete congeladas exactas. Inventario: **5355/5355**, cero diferencias SHA/tamaño; única adición posterior: `root-delivery-custody.json`. |

**Evidencia entregada, no reejecutada por esta lente:** JUnit final **426 PASS / 2 skips**, exit 0; dos suplementos HTTP con MockTransport separados. No acredita HTTP real, GPU ni aceptación completa. No reabro los hallazgos anteriores: el nuevo Important deriva de compartir la Session en este delta.