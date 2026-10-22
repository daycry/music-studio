**Lente A · U3/component-inspection1: 0 Critical · 1 Important · 0 Minor.** T-04 sigue abierta; esta entrega no acredita sus ocho criterios completos.

Leídos el diff U3, las ocho fuentes actuales, los tests, el brief, el plan, el ledger y las decisiones aplicables. Los ocho SHA-256 actuales coinciden con el freeze.

| T-04 → criterio de aceptación | Resultado de esta revisión | Evidencia |
|---|---|---|
| CA1 · Carriles, prioridad/FIFO, fechas y beats CPU sin descargar GPU | ✓ Parte U3: beats CPU y ausencia de unload comprobadas por assertions. Criterio global abierto. | `apps/server/tests/test_queue_references.py:139`; `apps/server/app/queue/dispatcher.py:87` |
| CA2 · Protocolo `EngineBackend` y backend HTTP | ✓ El diff conserva el protocolo y reserva `post.audio` para el server. Evidencia anterior U1/U2, sin nueva certificación HTTP. | `apps/server/app/queue/dispatcher.py:178` |
| CA3 · Cadena atómica N → post → N beats y referencias | ✓ Construcción, índices, semillas, rollback y resolución del intento ganador cubiertos. Post real T05 pendiente. | `apps/server/app/queue/chains.py:176`; `apps/server/tests/test_queue_chains.py:59`; `apps/server/tests/test_queue_references.py:76` |
| CA4 · Resolver por tarea verificada | ✓ Negativas de descriptor, parámetros, modo y pertenencia; referencias comprobadas antes de reservar y nuevamente bajo writer. | `apps/server/tests/test_queue_chains.py:104`; `apps/server/app/queue/admission.py:249` |
| CA5 · Unload y comprobación de VRAM libre | ✓ El diff conserva las comprobaciones anteriores; no acredita GPU real. | `apps/server/app/queue/dispatcher.py:119` |
| CA6 · NDJSON, cursor, progreso y bus | ✓ Sin modificación de implementación U2; no sustituye su aceptación previa ni acredita SSE de producto. | `apps/server/app/queue/events.py:75` |
| CA7 · Retryable, máximo y offload | ✓ Sin modificación de política U2. El guard nuevo impide reemplazar un intento preparado incierto. | `apps/server/app/queue/manual_retry.py:49`; `apps/server/tests/test_queue_manual_retry.py:209` |
| CA8 · Recuperación, reintento manual y variantes | ✗ El reintento exige que la generación esté `failed`, aunque los takes pueden fallar posteriormente en post-proceso. I-01 continúa pendiente. | `apps/server/app/queue/manual_retry.py:44` |

| Comprobación transversal | Resultado |
|---|---|
| Tareas declaradas hechas | ✓ Ninguna tarea se cierra en este diff. T-04 permanece `en-progreso`, ocho CA sin marcar: `tasks.md:171`, `tasks.md:183`. |
| Alcance y `Archivos` | ✓ Ocho rutas corresponden exactamente a U3 aprobada: tres módulos, admission/dispatcher y tres tests. `scope.json` declara ocho dentro y cero fuera; lectura contrastada con `dispatcher-unit-boundaries.md:11` y `tasks.md:177`. |
| Tests y cobertura | ✗ Falta el escenario de A1-01. Los demás comportamientos U3 examinados tienen assertions funcionales, no solo presencia de símbolos. |
| Constitución explícita | ✓ Sin infracción identificada de pertenencia, preservación de takes, escritura exclusiva del server, carriles o derechos: `docs/CONSTITUTION.md:10`, `:11`, `:18`, `:20`, `:43`. |
| Verificación declarada ejecutada | No aplica el gap de cierre sin evidencia: T-04 no está completada. El baseline entregado **no equivale** al comando exacto de `tasks.md:180`; esa verificación final permanece pendiente. |
| Generados y documentación E2/E3 | No aplica el chequeo interop: ninguna ruta del diff pertenece a `commands/`, `agents/` o `hooks/`. No cambia un contrato generado. Los límites T05/I-01 siguen explícitamente documentados. |
| TDD | ✓ RED funcional registrado: cadena unsupported, referencias vacías, admisión todavía bloqueada, retry unsupported y ACK incierto `DID NOT RAISE`. Los errores de imports/fixtures no cuentan como RED de producto. |

**A1-01 · Important — Reintento manual bloqueado tras fallo de post-proceso.**

- **Requisito:** `tasks.md:190` y `docs/arquitectura/sistema.md:100`: nuevo job con la misma request, reutilizando únicamente takes failed.
- **Código:** `apps/server/app/queue/manual_retry.py:44` rechaza cualquier generación cuyo estado no sea `failed`.
- **Escenario:** generación termina con `done` durable y queda `succeeded` (`apps/server/app/queue/events.py:76`). Después falla `post.audio` y quedan takes failed. Reintentar la generación se rechaza; reintentar el job `post.audio` tampoco sirve, porque `validate_request` exige una tarea musical.
- **Test que oculta el caso:** `apps/server/tests/test_queue_manual_retry.py:183` anuncia un fallo T05 posterior al éxito GPU, pero llama a `failed(...)`, que también cambia artificialmente la generación a `failed` en la línea 20.
- **Prueba del revisor:** control en memoria sobre `_selection`, con sesión sintética y generación `succeeded`: devuelve `Owned failed generation required` antes de seleccionar takes. **No es una prueba SQLite/T05 nativa.** La relación entre etapas está comprobada estáticamente.

Cobertura oficial contrastada con `coverage-final.json`, configuración sin exclusiones y SHA de las cinco fuentes completas:

| Fuente | Cobertura completa |
|---|---:|
| chains.py | 98,80 % |
| references.py | 83,56 % |
| manual_retry.py | 92,96 % |
| admission.py | 94,06 % |
| dispatcher.py | 89,63 % |

El trace vigente corresponde a **`baseline-final2`**, exit 0: **471 PASS, 2 SKIP**, del 04:39:02 al 04:41:41 UTC. `baseline-current` conserva la ejecución fallida anterior; no se utilizó como gate. No ejecuté suites, regeneraciones ni escrituras. T05 real, E2E, Docker, GPU, calidad e I-01 permanecen pendientes; contadores U1/U2 conservados.