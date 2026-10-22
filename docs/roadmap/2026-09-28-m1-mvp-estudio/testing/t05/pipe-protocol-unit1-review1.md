# Protocolo CPU — revisión1

A/B/C/D: **0Critical/0Important/0Minor**. QA independiente siguiente; transporte puro no prueba custodia ni slots.

### A

**Lente A · revisión 1: sin gaps Critical, Important ni Minor en la unidad entregada.** Esto no acredita el cierre de T-05.

Leído el diff completo: `pipe_protocol.py` (350 líneas) y `test_worker_pipe_protocol.py` (554 líneas). Ambos coinciden con las fuentes congeladas y los inputs de la corrida vigente.

| T-05 → criterio de la unidad IPC | Resultado | Evidencia fichero:línea |
|---|---|---|
| Sobre cerrado, identidad/epoch correlacionados y secuencia estricta | ✓ | `pipe_protocol.py:110`, `:117`, `:232`; tests `test_worker_pipe_protocol.py:140`, `:149`, `:306` |
| JSON UTF-8 estricto; rechazo de duplicados, no finitos, objetos ejecutables y claves prohibidas | ✓ | `pipe_protocol.py:72`, `:157`, `:170`; tests `test_worker_pipe_protocol.py:177`, `:200`, `:247`, `:253` |
| Límites de frame, total por dirección, profundidad, colecciones y cadenas | ✓ | `pipe_protocol.py:23`, `:137`, `:226`; tests `test_worker_pipe_protocol.py:218`, `:285`, `:390`, `:481`, `:513` |
| Direcciones, orden, 64 resultados por toma y terminal global único | ✓ | `pipe_protocol.py:242`; tests `test_worker_pipe_protocol.py:322`, `:330`, `:344`, `:368`, `:501` |
| Decodificación fragmentada; comprobación del prefijo antes de copiar el cuerpo | ✓ | `pipe_protocol.py:304`; tests `test_worker_pipe_protocol.py:62`, `:87`, `:107`, `:409`, `:549` |
| Entrega válida anterior al error, cuentas conservadas y decoder inutilizable tras fallo | ✓ | `pipe_protocol.py:329`, `:334`; tests `test_worker_pipe_protocol.py:421`, `:436`, `:530` |
| EOF parcial explícito; transporte separado de autoridad de negocio y custodia | ✓ | `pipe_protocol.py:8`, `:204`, `:341`; tests `test_worker_pipe_protocol.py:267`, `:468` |

| Comprobación solicitada | Resultado |
|---|---|
| **1. Tareas hechas y criterios completos** | ✓ Estado honesto: T-05 continúa `en-progreso` (`tasks.md:198`). Sus CA de post-proceso/publicación, `ready`/beats y limpieza/fallo siguen **✗ pendientes** (`tasks.md:211–213`); esta entrega no los declara cumplidos. |
| **2. Alcance y `Archivos`** | ✓ Los dos archivos pertenecen al worker y sus tests, declarados en `tasks.md:204`. Encajan con la secuencia del plan (`improvement-plan.md:64`) y la primera unidad de ADR-0057 (`ADR-0057…md:35`). `scope.json:7` enumera ambos; `:10` no registra archivos fuera de alcance. |
| **3. Tests, cobertura y TDD** | ✓ Lectura de assertions y límites realizada. Corrida **final-current-official: 110 passed, exit 0**. Cobertura del único módulo productivo cambiado: **238/240 = 99,1667 %, cero exclusiones**; análisis del `.coverage` original coincide con el JSON. Siete RED funcionales con argv, UTC, exit 1, JUnit, salida original y snapshots antes/después cotejados; no se cuentan errores de colección ni correcciones de fixtures. |
| **4. Constitución explícita** | ✓ Sin infracciones detectadas. Solo stdlib, sin BD, pickle, pesos, servicios ni contratos públicos alterados. Contrastado con `docs/CONSTITUTION.md:18`, `:24`, `:25`, `:33`, `:35`, `:37`. |
| **5. Verificación de tareas cerradas** | No aplica al cierre: T-05 permanece abierta. Los comandos de `tasks.md:207–208` **no quedan acreditados por los 110 tests dedicados**. No los ejecuté para sustituir evidencia ausente. |
| **6. Generados y documentación E2/E3** | No aplica: el diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador interop. Tampoco cambia contratos públicos generados. |

**Gaps: ninguno.** Evidencia ejecutada por este revisor: cotejos de hashes, diff, snapshots, JUnit y análisis de cobertura en modo lectura. Las suites son evidencia original de la entrega; no las repetí. Custodia nativa, pipes físicos, CPU2, publicación, Docker y E2E siguen pendientes.

### B

**Sin defectos de corrección encontrados.** Lente B, primera revisión, limitada a los dos ficheros nuevos de unit1.

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| JSON estricto, tipos y límites | ✓ | `apps/server/app/worker/pipe_protocol.py:72` |
| Framing y entradas malformadas | ✓ | `apps/server/app/worker/pipe_protocol.py:183` |
| Correlación, secuencia, dirección y terminal único | ✓ | `apps/server/app/worker/pipe_protocol.py:232` |
| Contadores conservados tras rechazo | ✓ | `apps/server/app/worker/pipe_protocol.py:226` |
| Fragmentación, entrega anterior al fallo y bloqueo posterior | ✓ | `apps/server/app/worker/pipe_protocol.py:304` |
| Reentrada y EOF truncado | ✓ | `apps/server/app/worker/pipe_protocol.py:341` |

Gaps: **Critical 0 · Important 0 · Minor 0**.

Evidencia registrada cotejada: fuentes actuales idénticas al freeze; 110 tests aprobados; cobertura del módulo completo **238/240 (99,17 %), cero exclusiones**; siete RED funcionales con inputs, argv, UTC, salida y JUnit originales.

Comprobación propia ejecutada en memoria: **228 fronteras de fragmentación**, entrega válida antes de secuencia inválida y bloqueo tras fallo, todas correctas. Sin repetir la suite ni escribir archivos.

Esto no acredita pipes nativos, custodia, publicación ni cierre completo de T-05.

### C

**Sin hallazgos de seguridad introducidos o reabiertos.** Critical: 0 · Important: 0 · Minor: 0.

Alcance: los dos ficheros nuevos de `scope.diff`, leídos completos y cotejados con los hashes actuales y el freeze. Selector automático C: `false`; revisión suplementaria por la frontera de confianza padre/hijo.

Referencias de la tabla relativas a `apps/server/app/worker/pipe_protocol.py`.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin sumideros de ejecución | `pipe_protocol.py:137`, `pipe_protocol.py:177`: serialización y parsing JSON |
| Deserialización insegura | ✓ Sin objetos ejecutables; rechaza duplicados y números no finitos | `pipe_protocol.py:157`, `pipe_protocol.py:177` |
| Autenticación y sesión | ✓ Correlación, secuencia y dirección comprobadas; epoch explícitamente no autentica | `pipe_protocol.py:10`, `pipe_protocol.py:226`, `pipe_protocol.py:238` |
| Secretos hardcodeados o exposición | ✓ Sin credenciales nuevas; errores sin contenido recibido y filtrado recursivo de claves | `pipe_protocol.py:51`, `pipe_protocol.py:100` |
| Path traversal y SSRF | ✓ Sin acceso a rutas ni peticiones de red | `pipe_protocol.py:16`, `pipe_protocol.py:177` |
| Permisos/autorización | ✓ El transporte no concede autoridad de publicación; DTO pendientes de validación por el padre | `pipe_protocol.py:8`, `pipe_protocol.py:201` |
| Recursos y entradas hostiles | ✓ Comprueba presupuesto antes de copiar el cuerpo; conserva cuentas aceptadas y bloquea el decoder tras error | `pipe_protocol.py:221`, `pipe_protocol.py:315`, `pipe_protocol.py:332` |

Evidencia **archivada**, no ejecutada por este revisor: JUnit 110 PASS, exit 0 y cobertura del módulo completo 238/240 = **99,1667 %**, cero exclusiones; fuentes antes/después/actuales coincidentes. Los siete RED registran fallos funcionales, sin errores de colección.

Revisión estática y estrictamente de lectura. No acredita pipes físicos, custodia de procesos, publicación ni cierre de T05.

### D

**Sin hallazgos de rendimiento.** Gaps: Critical 0 · Important 0 · Minor 0.

| Criterio | Resultado | Evidencia |
|---|---|---|
| N+1 | ✓ | `pipe_protocol.py:232`: sin consultas ni acceso a BD. |
| Bloqueos síncronos | ✓ | `pipe_protocol.py:304`: procesamiento en memoria, sin E/S ni esperas. |
| Trabajo repetido | ✓ | `pipe_protocol.py:170`, `:233`: doble validación lineal; sin degradación demostrada con carga real. |
| Escalado y copias | ✓ | `pipe_protocol.py:316`: acumulación incremental, sin concatenación cuadrática; límites de 256 KiB/frame y 4 MiB/dirección. |

Revisados los dos archivos completos del diff capturado; hashes actuales coinciden con el freeze. Activación D: patrón `worker` en ambas rutas, según `lens-selection.json`.

Evidencia de entrega comprobada: 110 PASS y cobertura del módulo completo 238/240 (**99,1667 %**), cero exclusiones. Revisión estática y lectura de originales; no ejecuté tests ni benchmarks. Esto no acredita rendimiento del worker integrado ni cierre de T05.