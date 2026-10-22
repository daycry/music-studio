**Lente A · T04 U2 · inspección 2: 0 Critical / 1 Important / 0 Minor.** Dictamen limitado al componente; no acredita U3 ni el cierre de T-04.

| T-04 → criterio de aceptación | Resultado | Evidencia fichero:línea |
|---|---|---|
| Carriles, prioridad/FIFO y `not_before` | ✗ La prioridad no se conserva entre reintentos y jobs nuevos | `runtime.py:431`; `retry.py:89`; gap A2-01 |
| Protocolo `EngineBackend` | ✓ En el componente revisado | `runtime.py:14`, `runtime.py:245` |
| Cadena generación → post → beats | Pendiente, correctamente abierta | `tasks.md:185`; U3 fuera de esta entrega |
| Resolver por tarea verificada | ✓ Validación fresca antes de reservar | `runtime.py:385`; `test_dispatcher_retry.py:61` |
| Unload y VRAM antes de cambiar engine | ✓ Corrección de residencia tras ACK exacto; siguiente despacho ejercitado | `runtime.py:245`; `test_dispatcher_retry.py:527` |
| NDJSON, cursor y bus interno | ✓ Conservados en esta corrección; criterio general abierto | `runtime.py:184`; `runtime.py:188` |
| Retry durable, presupuesto y offload | ✓ Para el alcance U2 revisado | `retry.py:31`, `retry.py:140`; `test_dispatcher_retry.py:770` |
| Recuperación con mismo ID/payload | ✓ Reenvío conservado; manual/batch siguen pendientes | `runtime.py:153`, `runtime.py:161`; `test_dispatcher_retry.py:527` |

| Comprobación transversal | Resultado |
|---|---|
| Tareas completadas y verificaciones | ✓ T-04 sigue `en-progreso`, con ocho CA abiertos (`tasks.md:171`). No exige cerrar mediante la suite parcial ni presenta su Verificación contractual como ejecutada. |
| Alcance y `Archivos` | ✓ Cinco fuentes corresponden a cola, tests e integración de lifespan prevista. `scope.json`: cinco dentro, cero fuera, cero archivos excluidos. |
| Tests y cobertura actual | ✓ Lectura de ambos tests completos. Traza oficial normalizada contra fuentes actuales: `main` **96,1165 %**, `retry` **94,1176 %**, `runtime` **89,3471 %**; cero exclusiones por módulo. |
| TDD | ✓ Evidencias RED funcionales diferenciadas de controles verdes y errores de fixture; originales, argv, UTC y JUnit conservados. No certifica retrospectivamente la historia inicial. |
| Constitución | ✓ Sin nueva violación explícita detectada: escritura exclusiva del server, residencia única y cierre con Verificación (`docs/CONSTITUTION.md:18`, `:21`, `:33`). |
| Generados y documentación E2/E3 | No aplica al exportador interop: el diff no toca `commands/`, `agents/` ni `hooks/`. Sin cambio contractual que requiera regeneración detectado. |

**A2-01 · Important — Los reintentos saltan la prioridad de la cola normal.**

Ubicación: `apps/server/app/queue/runtime.py:431`, `:397`; `apps/server/app/queue/retry.py:89`. Requisito: `docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:183`, «Prioridad y después FIFO».

Escenario concreto: GPU libre, un job `batch` fallido con retry elegible y un job `interactive` encolado, ambos ejecutables. `_run()` reserva y envía primero el retry mediante `_retry()`; posteriormente llama al despacho normal, que encuentra la GPU ocupada. El orden de `candidate_batches()` compara únicamente jobs `failed`, por lo que tampoco preserva FIFO entre un retry y un job nuevo de igual prioridad. Los tests de FIFO en `test_dispatcher_retry.py:218` y `:311` comparan solamente reintentos.

**Evidencia del gap: lectura estática del flujo**, sin reproducción funcional ejecutada por este revisor.

Verificación propia exclusivamente de lectura: cinco fuentes congeladas y 87 fuentes de entrega sin drift; cobertura oficial recalculada en memoria coincidente. Los **386 PASS / 2 skips** y los **2 HTTP PASS complementarios** son evidencia del implementador, no suites reejecutadas por la lente.