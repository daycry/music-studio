# Revisión de dos lentes — intento 2/3: bus y framing SSE

A/B/C/D: **0 Critical · 0 Important · 0 Minor**. A01 corregido; historial del intento1 conservado. Revisión cerrada, QA y aceptación pendientes.

El baseline original mantiene **452 PASS/1 FAIL, exit1**. Los diagnósticos no explican el timeout801; no se cambia el plazo10s ni se etiqueta flaky. La cobertura completa de esa corrida fallida es una medición, no un gate verde.

## Lente A

**Lente A · intento 2/3 · T-06/U1: 0 Critical, 0 Important, 0 Minor nuevos. A01 corregido.** Esta conclusión cubre bus y adaptador puro; **no acepta T-06 ni la baseline fallida**.

| T-06 → criterio de aceptación | Resultado | Evidencia fichero:línea |
|---|---|---|
| Sobre `{id, type, ts, data}` y tipos públicos | ✓ En U1. `entity.updated` publica exactamente `data.type/id`; descarta los campos privados inventados. | `apps/server/app/sse.py:202,235,268`; `apps/server/tests/test_sse_frames.py:198` |
| Keep-alive cada 15 s | ✗ Pendiente de integración: hay constante y comentario SSE, pero no temporizador. No es gap de esta entrega parcial. | `apps/server/app/sse.py:12,351`; `tasks.md:230` |
| Replay de eventos retenidos | ✓ En U1. Registro y replay comparten lock; los tests comprueban orden, handoff con hilos reales y copias independientes. HTTP `Last-Event-ID` queda pendiente. | `apps/server/app/queue/events.py:65,82,195`; `apps/server/tests/test_sse_bus.py:23,180` |
| Estado actual cuando se agota el buffer | ✗ Pendiente: se devuelve `ResetPlan`, sin snapshot SQL. No es gap de esta entrega parcial. | `apps/server/app/queue/events.py:77,80`; `apps/server/app/sse.py:131`; `tasks.md:231` |

| Comprobación transversal | Resultado y evidencia |
|---|---|
| Tareas hechas realmente implementadas | ✓ Sin cierre ficticio: T-06 está `en-progreso` y ambos CA siguen abiertos (`tasks.md:218,230,231`). |
| Alcance y `Archivos` | ✓ Los cuatro ficheros corresponden a `tasks.md:224` y a la unidad bus/framing prevista en `improvement-plan.md:69` y ADR-0056:29. Scope capturado: 4 dentro, 0 fuera; configuración sin exclusiones añadidas. |
| Tests de U1 | ✓ Lectura completa de ambos tests: replay/handoff, overflow, cierre/cancelación, límites, filtros, privacidad, cursores y frames. `test_sse_bus.py:23,57,86,107,133,180`; `test_sse_frames.py:37,80,116,198,244,269`. |
| Cobertura actual | ✓ **Medición**, no aceptación: `events.py` **195/203 = 96,0591 %**; `sse.py` **202/208 = 97,1154 %**; cero exclusiones por fichero. JSON, argv y snapshots pertenecen a la misma corrida oficial fallida; las cuatro fuentes coinciden por SHA-256 con las actuales. |
| TDD | ✓ Seis RED funcionales originales con argv/UTC/JUnit. Para A01, RED2: PID24716, exit1, dos fallos de igualdad del frame antes del fix; GREEN posterior: 28 PASS, exit0. No son errores de colección. |
| Constitución explícita | ✓ Sin violaciones nuevas detectadas. Se conservan autoridad del server y terminales, estado sin cierre ficticio y contrato documentado (`docs/CONSTITUTION.md:18,19,33,35,37,42`). |
| Verificación declarada | N/A para cierre: T-06 continúa abierta. No consta como cumplido el comando literal de `tasks.md:227`; no lo ejecuté para sustituir evidencia. |
| Generados y documentación E2/E3 | Interop **no aplica**: el diff no toca `commands/`, `agents/` ni `hooks/`. La descripción vigente reconoce expresamente los límites de U1 (`improvement-plan.md:69`; ADR-0056:29,31). |

**Gaps nuevos: ninguno.** A01 del intento 1 queda resuelto; se conserva su historial y el contador formal.

**Limitación de aceptación:** `final-official/command-original.json` acredita **pytest exit1**, con **452 PASS / 1 FAIL** en `test_global_busy_gpu_negative_once_and_available_cpu_native[801]`. La causa original sigue **UNKNOWN**; los diagnósticos posteriores no la explican ni sustituyen esa baseline. QA independiente y aceptación permanecen pendientes.

Revisión estática y cotejos ejecutados en memoria; no reejecuté suites, escribí ficheros ni modifiqué el ledger.

## Lente B

**Sin defectos de corrección detectados.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Replay y alta atómica; límites del cursor | ✓ | `apps/server/app/queue/events.py:65` |
| Overflow, cancelación, cierre y notificaciones | ✓ | `apps/server/app/queue/events.py:130`, `:148`, `:180` |
| Copias independientes y conservación del orden | ✓ | `apps/server/app/queue/events.py:117`, `:195` |
| Filtrado, validación y frames acotados | ✓ | `apps/server/app/sse.py:106`, `:202`, `:286` |
| `entity.updated` conserva `data.type/id` | ✓ | `apps/server/app/sse.py:222`, `:241` |
| Compatibilidad de `EventConsumer` | ✓ AST idéntica al preimage | `apps/server/app/queue/events.py:211` |

Revisión estática del diff completo y fuentes actuales; cotejos ejecutados de hashes, AST y evidencias originales, sin repetir suites ni escribir archivos.

Cobertura completa de la única traza oficial: `events.py` **195/203 (96,06 %)** y `sse.py` **202/208 (97,12 %)**, cero exclusiones. Esa corrida conserva **452 PASS / 1 FAIL, exit 1**: el timeout original sigue con causa desconocida. Este veredicto se limita al bus y adaptador puro; **no acredita QA ni cierre de T06**.

## Lente C

**Lente C · revisión 2/3: sin hallazgos.** 0 Critical · 0 Important · 0 Minor.

Revisado el diff completo capturado de cuatro archivos contra U1 y las fuentes actuales; sus SHA-256 coinciden con el freeze. El selector dio `C=false`; root añadió C por privacidad del framing y límites de filtros.

| Criterio | Resultado y evidencia fichero:línea |
|---|---|
| Inyección SQL/comando/plantilla | Sin nuevos puntos de ejecución. `apps/server/app/queue/events.py:104`, `apps/server/app/sse.py:202`. |
| Inyección SSE | Cursor y tipo restringidos; JSON escapa CR/LF del texto. `apps/server/app/sse.py:55`, `:213`, `:340`. |
| Autenticación/sesión | Sin cambios. `TrustedScope` exige permisos previamente resueltos; no acredita autenticación HTTP. `apps/server/app/sse.py:66`. |
| Permisos/autorización | Replay y entrega filtran por IDs preautorizados; delta requiere permiso explícito. `apps/server/app/queue/events.py:82`, `:129`; `apps/server/app/sse.py:106`, `:261`, `:281`. |
| Secretos/privacidad | Sin credenciales hardcodeadas; allowlist excluye `engine_token`, mensajes, peticiones, resultados y telemetría. `apps/server/app/sse.py:224`, `:233`. |
| Deserialización insegura | Tipos JSON estrictos y límites antes de copiar; sin carga ejecutable. `apps/server/app/sse.py:138`; `apps/server/app/queue/events.py:111`. |
| Path traversal/SSRF | Sin nuevas operaciones de archivos o red. `apps/server/app/queue/events.py:104`, `apps/server/app/sse.py:329`. |
| Agotamiento de recursos | Suscriptores, pendientes, callbacks y frames acotados. `apps/server/app/queue/events.py:68`, `:130`, `:148`; `apps/server/app/sse.py:325`. |

**Evidencia del revisor:** lectura estática y cotejo ejecutado de hashes; sin sondas funcionales ni suites nuevas. No se identificó escenario concreto de explotación ni CWE que reportar.

**Evidencia de entrega inspeccionada:** RED funcional de dos casos, PID 24716, exit 1, con argv/UTC/JUnit/logs. Corrida oficial: **452 PASS/1 FAIL, exit 1**. Cobertura completa de esa única traza: `events.py` **195/203 (96,0591 %)** y `sse.py` **202/208 (97,11538 %)**, cero exclusiones. Son mediciones de una suite fallida, no aceptación QA.

Alcance exclusivo: bus y adaptador puro. Se conserva el veredicto anterior; este resultado no cierra T06 ni acredita endpoint, snapshots, autorización SQL o E2E.

## Lente D

**Sin hallazgos de rendimiento.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Evidencia estática, fichero:línea | Resultado |
|---|---|---|
| N+1 | `apps/server/app/queue/events.py:128` | El fan-out nuevo no consulta SQL; `EventConsumer` permanece sin cambios. |
| Bloqueos y callbacks | `apps/server/app/queue/events.py:148`, `:180` | Espera async y notificaciones coalescidas; como máximo 32 suscripciones/notificaciones contabilizadas. Sin degradación acreditada con carga real. |
| Trabajo repetido | `apps/server/app/sse.py:26`, `:329` | Patrones precompilados y ensamblado mediante `join`; recorridos lineales acotados por payload/frame. |
| Crecimiento con volumen | `apps/server/app/queue/events.py:31`, `:82`, `:130` | Replay predeterminado de 256 registros y 64 pendientes por suscriptor; el histórico total no incrementa estos recorridos. |

Motivo de activación: selector `lens-selection.json`, patrón `queue` en `apps/server/app/queue/events.py`.

Leído el diff completo de cuatro ficheros y cotejados sus SHA-256 actuales con el freeze. **No ejecuté pruebas de carga ni repetí suites**; el veredicto se basa en inspección estática.

Verificados los originales: cobertura WHOLE de `events.py` **195/203 (96,06 %)** y `sse.py` **202/208 (97,12 %)**, sin exclusiones, procedente de la corrida **452 PASS / 1 FAIL, exit 1**. El timeout conserva causa **UNKNOWN**: no acredita un defecto de rendimiento ni permite cerrar QA o T06.

## Límites

No acredita endpoint, heartbeat efectivo, snapshot SQL, autenticación, cliente, E2E ni cierre de T06/M1. Fuentes4 exactas al cerrar; la implementación independiente de custodia Windows no forma parte de este diff.
