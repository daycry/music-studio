# SSE U1 — revisión1

**0Critical/1Important/0Minor**: A01 forma de entity.updated confirmada. B/C/D sin defectos adicionales. Counter1 se conserva; fix, revisión2 yQA siguen. No aceptaciónT06/M1.

### A

**Lente A · intento 1 · T-06/U1: 0 Critical, 1 Important, 0 Minor.** Revisión limitada a los cuatro ficheros congelados; sus hashes siguen coincidiendo con la entrega y la traza oficial.

| Tarea → criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| T-06 → sobre `{id,type,ts,data}` y tipos públicos | ✗ Parcial: `entity.updated` pierde los campos documentados `{type,id}` | `apps/server/app/sse.py:223,235`; `docs/arquitectura/convenciones.md:34` |
| T-06 → keep-alive cada 15 s | ✗ Pendiente fuera de U1: existen constante y comentario puro, sin temporizador | `apps/server/app/sse.py:12,348`; `tasks.md:230` continúa abierto |
| T-06 → replay de eventos retenidos | ✓ Para U1: replay y registro bajo el mismo lock, IDs ordenados y copias independientes | `apps/server/app/queue/events.py:65,82,195`; `test_sse_bus.py:23,180` |
| T-06 → estado actual cuando expira el buffer | ✗ Pendiente fuera de U1: devuelve `ResetPlan`, sin snapshot SQL | `apps/server/app/queue/events.py:77,80`; `apps/server/app/sse.py:131`; `tasks.md:231` continúa abierto |
| U1 → overflow, cancelación, cierre y límites | ✓ | `apps/server/app/queue/events.py:68,130,148,167,203`; `test_sse_bus.py:86,107,133` |
| U1 → filtros, privacidad, cursor y framing acotado | ✓ Salvo la forma de `entity.updated` señalada arriba | `apps/server/app/sse.py:106,278,285,326`; `test_sse_frames.py:37,80,116` |

| Comprobación transversal | Resultado |
|---|---|
| Tareas declaradas completadas | ✓ No hay cierre de T-06 ni de sus CA; `tasks.md:218,230–231,1147` conserva el alcance parcial. |
| Alcance | ✓ Los cuatro cambios corresponden a `Archivos` (`tasks.md:224`) y a la secuencia U1 (`improvement-plan.md:69`, ADR-0056:29). Captura scope: 4 dentro, 0 fuera, 0 exclusiones efectivas. |
| Tests y cobertura | ✓ Lectura de ambos tests nuevos y cotejo byte a byte de los 15 tests ejecutados. Traza única: **428 passed**, exit **0**; `events.py` completo **195/203 = 96,0591 %**, `sse.py` completo **203/209 = 97,1292 %**, **cero exclusiones**. |
| TDD | ✓ Seis RED con argv/UTC/JUnit y snapshots íntegros: fallos funcionales, sin errores de colección. Baselines compilables identificadas; no se presentan como implementación nativa completa. |
| Constitución | ✓ Sin violaciones adicionales detectadas. `EventConsumer` conserva AST idéntica; se mantienen autoridad SQL y terminales (`CONSTITUTION.md:18–19`), estado sin cierre ficticio (:33) y separación del contrato público futuro (:35). |
| Verificación declarada | N/A para cierre: T-06 sigue abierta. La corrida privada oficial está acreditada, pero **no equivale** al comando literal de `tasks.md:227`; no lo ejecuté para sustituir evidencia. |
| Generados y documentación E2/E3 | Interop **no aplica**: el diff no toca `commands/`, `agents/` ni `hooks/`. OpenAPI tampoco cambia. La descripción de U1 es vigente; queda la discrepancia documental siguiente. |

**Gap A-01 · Important · pendiente**

- **Lugar:** `apps/server/app/sse.py:235`; test que consolida la discrepancia: `apps/server/tests/test_sse_frames.py:134`.
- **Requisito:** `docs/arquitectura/convenciones.md:34` declara `entity.updated {type, id}`.
- **Escenario reproducido por el revisor:** al encodificar un registro autorizado con `data={"type":"take","id":"take01"}`, el frame entrega únicamente `data={"entity_id":"take01"}`. La allowlist elimina ambos campos documentados y adopta `entity_type/revision` sin una decisión que sustituya esa forma.
- **Consecuencia:** el consumidor que siga el contrato vigente pierde el tipo y el ID esperado de la entidad. Corregir el adaptador y su test, o resolver explícitamente el contrato con la documentación correspondiente.

Las comprobaciones del revisor fueron de lectura y una sonda en memoria; no repetí la suite, no escribí archivos ni modifiqué el ledger. **Este veredicto no acepta T-06 completo ni sustituye QA.**

### B

**Sin defectos de corrección detectados en T06 U1.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Replay y alta atómica; cursores expirados/adelantados | ✓ | `apps/server/app/queue/events.py:61` |
| Overflow, cancelación, cierre y notificación acotada | ✓ | `apps/server/app/queue/events.py:139` |
| Copias independientes para publicación y replay | ✓ | `apps/server/app/queue/events.py:125` |
| Filtrado previo, adaptación y validación del framing | ✓ | `apps/server/app/sse.py:202`, `:278`, `:326` |
| Compatibilidad de EventConsumer | ✓ AST idéntica al preimage | `apps/server/app/queue/events.py:214` |

Cotejadas las cuatro fuentes actuales con el freeze y las copias oficiales. Evidencia original verificada: **428 PASS**, cobertura WHOLE de `events.py` **195/203 (96,06 %)** y `sse.py` **203/209 (97,13 %)**, ambas sin exclusiones; seis RED funcionales con argv, UTC, JUnit y logs.

Revisión estática y cotejos ejecutados en memoria; no reejecuté la suite ni modifiqué ficheros. El resultado se limita a U1 y no acredita integración HTTP, snapshots ni cierre de T06.

### C

**Sin hallazgos de seguridad en T06/U1.** Critical: 0 · Important: 0 · Minor: 0.

Revisados los cuatro ficheros del `scope.diff` capturado y sus fuentes actuales; sus SHA-256 coinciden con el freeze al inicio y al final. El selector automático devolvió C=false; root añadió esta lente por privacidad del framing y límites de autorización.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL, comando o plantilla | ✓ No se añaden consultas, ejecución de comandos ni plantillas. | `events.py:104`, `sse.py:202` |
| Inyección de frames SSE | ✓ Cursor y tipo restringidos; CR/LF del texto se escapan mediante JSON. | `sse.py:55`, `sse.py:202`, `sse.py:326` |
| Autenticación y sesión | ✓ Sin cambios en esta unidad. `TrustedScope` documenta que recibe permisos previamente resueltos. | `sse.py:66` |
| Permisos y autorización | ✓ Replay y entrega filtran por IDs preautorizados; owner/song complementan el filtro. El texto delta exige permiso explícito. | `events.py:82`, `events.py:128`, `sse.py:106`, `sse.py:278` |
| Secretos y privacidad | ✓ Sin credenciales hardcodeadas. La lista de campos públicos omite mensajes, peticiones, resultados y telemetría privados. | `sse.py:227` |
| Deserialización insegura | ✓ Sin pickle ni carga ejecutable; se restringen tipos, volumen y profundidad antes de copiar. | `sse.py:138`, `events.py:111` |
| Path traversal / SSRF | ✓ No se introducen accesos a rutas ni solicitudes de red. | `sse.py:326`, `events.py:104` |
| Agotamiento de recursos | ✓ Límites de suscriptores, pendientes y frames; notificaciones coalescidas. | `events.py:68`, `events.py:130`, `events.py:148`, `sse.py:286` |

**Evidencia ejecutada por este revisor:** probe en memoria, sin escrituras, que comprobó escape CR/LF, omisión de campos privados, filtrado de IDs ajenos y permiso delta; pasó. También confirmé que `EventConsumer` conserva su AST.

**Evidencia de entrega inspeccionada, sin repetir la suite:** argv, UTC, JUnit y logs originales de los seis RED funcionales; final oficial con 428 pruebas, cero fallos. Cobertura completa de esa única corrida: `events.py` 195/203 = 96,0591 %; `sse.py` 203/209 = 97,1292 %; cero exclusiones en ambos.

La conclusión cubre exclusivamente bus y framing. Endpoint, credencial pública, autorización SQL, snapshots y E2E permanecen pendientes; esta revisión no acredita el cierre de T06.

### D

**Sin hallazgos de rendimiento.** Critical: 0 · Important: 0 · Minor: 0.

Lente D activada por `apps/server/app/queue/events.py` (patrón `queue`). Revisados el diff completo de cuatro ficheros y las fuentes actuales, coincidentes con el freeze y la entrega oficial.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| N+1 | `events.py:104` | ✓ La publicación nueva no consulta SQL; `EventConsumer` queda fuera del cambio. |
| Bloqueos síncronos | `events.py:180` | ✓ Espera con `asyncio.Event`, sin sondeo ni E/S síncrona nueva. |
| Trabajo repetido | `events.py:128`, `sse.py:319` | ✓ Distribución limitada a 32 lectores; framing lineal con tamaño acotado. No hay degradación material demostrada. |
| Crecimiento con volumen | `events.py:82`, `events.py:130`, `sse.py:138` | ✓ Replay predeterminado de 256 registros, pendientes de 64 por lector y payload limitado en bytes, nodos y profundidad. |
| Notificaciones acumuladas | `events.py:148` | ✓ Callback coalescido por lector; las notificaciones pendientes cuentan para el límite de admisión. |

Evidencia de entrega cotejada: **428 PASS**, cobertura completa de `events.py` **195/203 (96,06 %)** y `sse.py` **203/209 (97,13 %)**, ambas sin exclusiones.

Revisión estática y comprobaciones de lectura; no ejecuté suites ni benchmarks. Este resultado corresponde exclusivamente a T06/U1.