**Lente A — T04 U1: 0 Critical / 1 Important / 0 Minor.** La entrega requiere resolver la discrepancia de evidencia TDD. T-04 permanece `en-progreso`, con sus ocho CA abiertos; esta inspección no sustituye la revisión formal 4 tras integración.

| T-04 → criterio de aceptación | Resultado dentro de U1 | Evidencia código/test |
|---|---|---|
| CA1: GPU1/CPU2, prioridad/FIFO, `not_before`, CPU sin descargar GPU | ✓ Implementación parcial conforme | `admission.py:94,113,138`; `test_dispatcher_admission.py:99,117,267,411` |
| CA2: protocolo de nueve operaciones y HTTP `/v1` | ✓ Implementado | `backends/protocol.py:48`; `backends/http.py:140`; `test_queue_backend.py:56,206` |
| CA3: cadenas generación → post → beats | ✗ Pendiente U3; no constituye gap de U1 | `delivery.md:39`; `test_dispatcher_admission.py:246` |
| CA4: resolver por tarea verificada y catálogo en caché | ✓ Implementado | `resolver.py:231,251,278`; `test_queue_resolver.py:105,146,192,219` |
| CA5: unload y comprobación de memoria libre | ✓ Implementado para residencia observada propia | `dispatcher.py:75,91,110`; `test_dispatcher_admission.py:341` |
| CA6: eventos, cursor, progreso y SSE | ✗ Integración pendiente U2; transporte NDJSON presente | `backends/http.py:220`; `test_queue_backend.py:149` |
| CA7: retries y offload único | ✗ Pendiente U2; no constituye gap de U1 | `delivery.md:47` |
| CA8: recuperación, identidad durable y retry manual | ✓ Reserva inicial e incertidumbre; ✗ recuperación/manual pendientes U2/U3 | `admission.py:178,201`; `dispatcher.py:128,145`; `test_dispatcher_admission.py:148` |

Las rutas abreviadas anteriores pertenecen a `apps/server/app/queue/` y `apps/server/tests/`.

| Comprobación transversal | Resultado |
|---|---|
| Cierres declarados | ✓ U1 no declara T-04 completada; `tasks.md:171,183` conserva estado y CA abiertos. |
| Alcance | ✓ Diez fuentes nuevas coinciden íntegramente con `scope.diff`; corresponden a `Archivos` en `tasks.md:177`, fase 2 del plan y ADR-0047. `engine_client.py` permanece intacto. |
| Tests y cobertura | ✓ Leídos los tres tests completos. Evidencia original: **98 propios PASS**, **25 vecinos PASS**, separados. Cobertura completa: admisión **93,04 %**, HTTP **92,17 %**, protocolo **100 %**, dispatcher **86,52 %**, resolver **83,76 %**; cero exclusiones. |
| Constitución | ✓ Sin infracción identificada en este alcance: escritura del server, carriles, capacidades, identidad ULID y presupuesto libre−margen (`CONSTITUTION.md:18,20,21,22,36`). |
| Verificación de tarea cerrada | N/A: T-04 sigue abierta. La ejecución focal de U1 no acredita la verificación completa de `tasks.md:180`; no la ejecuté para suplir evidencia. |
| Generación/descripción E2/E3 | N/A: el diff no toca `commands/`, `agents/` ni `hooks/`. |
| Custodia | ✓ Comprobación ejecutada en solo lectura: 11 fuentes y sus copias exactas, 65 protegidas sin drift y 10 fuentes de esquema aceptadas intactas. |

**Gap Important — A-U1-01: RED de presencia presentado como RED funcional.**

En [delivery.md:33](.cache/dev-cycle/m1/t04-dispatcher-u1-context1/delivery.md:33) y `:35` se califican como funcionales ejecuciones que fallan exclusivamente en `find_spec`, antes de comprobar el comportamiento exigido. Contradice el requisito explícito de RED funcional anterior al código del encargo y [task-brief.txt:168](.cache/dev-cycle/m1/t04-u1-component-inspection1/task-brief.txt:168).

Escenario concreto: `red-capacity-corrected` registra **2 fallos** porque falta `app.queue.admission`; ninguno alcanza la carrera GPU1/CPU2. `red-dependencies-corrected` registra **4 fallos** por la misma presencia ausente, sin evaluar dependencias. También ocurre en `red-1…7`, `red-10` y `red-never_unloads_unknown_model_or_cpu`. Contrasté mensajes originales, JUnit, argv, UTC y secuencia de creación de fuentes.

Los RED posteriores de soporte, política nativa, residencia, FIFO fraccional y semilla NULL sí contienen fallos funcionales concretos; no subsanan retrospectivamente los anteriores. La cobertura y el GREEN actual acreditan comportamiento presente, pero no ese requisito TDD.

No ejecuté suites ni probes de producto; las comprobaciones propias fueron de lectura, hashes, diff y artefactos originales. Wheel, imports nativos y Docker siguen pendientes de QA independiente.