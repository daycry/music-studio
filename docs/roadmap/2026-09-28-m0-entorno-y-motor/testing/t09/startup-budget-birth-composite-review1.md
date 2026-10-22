# U1 de arranque · revisión compuesta, intento 1

Ocho gaps Important y uno Minor. Seis defectos de lifecycle requieren reproducción conductual; además, cobertura y regresión actuales incumplen sus gates. El EOF anterior sigue sin causa demostrada. Sin aceptación.

## Lente A

**Lente A: U1 no conforme para aceptación. 0 Critical · 5 Important · 0 Minor.**

Revisión estática del diff compuesto de seis archivos contra las preimágenes genuinas del primer U1, el plan, el ledger y ADR-0059. Los seis SHA-256 actuales coinciden con el freeze. Las diferencias entre las preimágenes y el HEAD del fixture son únicamente de finales de línea.

| Criterio de revisión | Resultado | Evidencia |
|---|---|---|
| (1) Tareas declaradas hechas | ✓ Declaración correcta | `tasks.md:395`: T-09 sigue `en-progreso`; `tasks.md:2464`: U1 expresamente no aceptada. Ninguna tarea cerrada en este diff. |
| (2) Alcance y `Archivos` | ✓ | `tasks.md:401`, `improvement-plan.md:82`, `ADR-0059:35`: los cuatro módulos y dos tests pertenecen a U1. El packet de scope declara seis archivos y ninguno fuera de alcance. |
| (3) Tests y cobertura actual | ✗ | Leídos ambos tests completos. Final03 contiene los 26 casos nuevos aprobados, pero incumple cobertura y regresión: A-U1-04/05. |
| (4) Constitución explícita | ✓ | No identifico una violación constitucional introducida. `docs/CONSTITUTION.md:33` exige verificación para cerrar tareas; T-09 permanece abierta. |
| (5) Verificación de tareas cerradas | N/A | `tasks.md:403`: la verificación del benchmark continúa pendiente. No existe cierre que carezca de evidencia en este alcance. No la ejecuté. |
| (6) Generados y descriptores E2/E3 | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador interop. El plan y ADR describen U2–U4 como pendientes. |

**T-09 → criterios de aceptación del ledger**

| Criterio | Resultado en esta entrega |
|---|---|
| Matriz de configuraciones y duraciones (`tasks.md:408`) | ✗ Pendiente; U1 no la acredita. |
| Bind mount frente a copia (`tasks.md:409`) | ✗ Pendiente. |
| Descarga de Ollama y VRAM en reposo (`tasks.md:410`) | ✗ Sin nueva acreditación en U1. |
| Navegador abierto y observación del desbordamiento (`tasks.md:411`) | ✗ Sin nueva acreditación en U1. |
| Experimento opcional `torch.compile` (`tasks.md:413`) | N/A; opcional, no acreditado. |
| Recomendación argumentada con números (`tasks.md:414`) | ✗ Pendiente. |

Estos pendientes generales **no son gaps adicionales de U1** ni implican revisar U2–U4 anticipadamente.

| T-09 → requisito actual de U1 | Resultado | Fuente / test |
|---|---|---|
| Plazo absoluto, validación estricta y default convertido una vez | ✓ | `benchmark_startup.py:16`; `test_benchmark_startup_budget.py:10`. |
| Propagación en las entradas modificadas | ✗ Parcial | `benchmark_episode.py:533` transmite D; el cierre del constructor coordinado lo pierde: A-U1-01. |
| Nacimiento retenido y revocación irreversible | ✓ Para los escenarios comprobados | `benchmark_process.py:367,464`; `test_benchmark_birth_custody.py:72,262`. Popen/Job reales con demoras controladas; no syscall físicamente bloqueada. |
| Espera inicial de condición acotada | ✓ | `benchmark_coordinator.py:99`; `test_benchmark_birth_custody.py:224`. |
| Custodia UNKNOWN y reserva mientras existan actores pendientes | ✗ | A-U1-02/03. |
| Episodios con ventana original de dos segundos | ✓ | `benchmark_episode.py:566`; comprobación en `test_benchmark_birth_custody.py:194`. |
| Cobertura WHOLE ≥80 %, cero exclusiones y regresión completa | ✗ | A-U1-04/05. |

**Gaps**

| ID | Severidad | Fichero:línea | Escenario concreto y requisito incumplido |
|---|---|---|---|
| A-U1-01 | Important | `scripts/eval/benchmark_coordinator.py:376,381`; `scripts/eval/benchmark_process.py:700` | `super().__init__` termina dentro de D, pero la comprobación final espera una condición ocupada hasta agotarlo. El `except` llama a `close()` sin transmitir D; como el constructor base terminó correctamente, falta `_startup_cleanup_deadline_ns` y se concede una espera nueva de **220 ms**. Incumple el presupuesto original de `ADR-0059:15,29`. |
| A-U1-02 | Important | `scripts/eval/benchmark_coordinator.py:392` | El predicado `pending` solo comprueba birth y cleanup. Si un actor de gate/evidence/activate sigue pendiente y esos dos threads ya terminaron, el `finally` puede poner `coordinator.active = None`, incluso con recursos UNKNOWN. Se libera la reserva sin comprobar `record.actors` ni cierre confirmado; contradice `ADR-0059:29`. |
| A-U1-03 | Important | `scripts/eval/benchmark_process.py:919,925,959` | Una consulta nativa puede continuar pendiente después del timeout mientras cleanup completa sus propias consultas. Cleanup cierra Job y handle de proceso **antes** de comprobar los actores pendientes. La referencia fuerte permanece, pero sus handles originales ya están cerrados mientras el actor todavía puede utilizarlos; UNKNOWN se determina después. Incumple la conservación de handles/transporte de `ADR-0059:27,29`. |
| A-U1-04 | Important | `.cache/dev-cycle/t09/startup-budget-birth-unit1-resume1/four-whole-official.json:53` | Coordinador **71,92623 %**, inferior al mínimo explícito de `ADR-0059:39` y `.claude/dev.json`. Cobertura WHOLE actual: startup **100 %**, process **84,27746 %**, episode **86,94853 %**; cero exclusiones en los cuatro. No procede sustituirla por promedio, líneas cambiadas o trazas históricas. |
| A-U1-05 | Important | `docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md:2464` | La regresión vigente termina exit **1**: **269 PASS, 1 FAIL, 30 ERROR**. El fallo funcional ocurre en `test_factory_owns_actual_workers_and_fresh_consumer_binding` durante consume con `worker_pipe_eof`; los 30 errores son del bootstrap `harness_module`, no fallos funcionales de producto. La entrega carece de una regresión completa conforme. |

La evidencia original confirma dos RED funcionales: nacimiento tardío y presupuesto del contexto, con argv, UTC y JUnit. Los intentos de colección/import y la primera fixture de propagación no se contabilizan como RED.

**Límites:** A-U1-01/02/03 son escenarios derivados de lectura estática, sin reproducción por este reviewer. Final03 usa UUID `8162851a-bc5a-4fe9-a1b8-938fb6d8e704`; contrasté su JSON oficial, argv, JUnit y mapa de fuentes. El diagnóstico posterior de un caso aprobado no prueba la causa original, no demuestra flakiness y no subsana la baseline fallida. No ejecuté suites, procesos nativos ni modificaciones.

## Lente B

**2 Important y 1 Minor; ningún Critical.** Hallazgos estáticos sobre las seis fuentes cuyo hash coincide con el freeze. Sin ejecutar tests ni procesos.

| Criterio | Gravedad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| Conservar la primera excepción | **Important · B-U1-01** | `scripts/eval/benchmark_process.py:408`, `:151` | El actor registra un fallo nativo antes del deadline, pero el caller vuelve a ejecutarse después de vencerlo. `record.check()` lanza antes de consultar `record.failure`; `_NativeAction.wait()` también comprueba la llegada tardía antes de `self.failure`. El caller recibe `WorkerDeadline` en lugar de la excepción original ya registrada. |
| Liberar la reserva tras resolver el nacimiento pendiente | **Important · B-U1-02** | `scripts/eval/benchmark_coordinator.py:389` | Un nacimiento excede el plazo y sigue pendiente durante el `finally`: se conserva `coordinator.active = self`. Más tarde terminan el nacimiento y su limpieza, pero ninguna ruta de finalización libera esa reserva. Otro `CoordinatedOwnedProcess` sobre el mismo coordinador recibe permanentemente `v3_parallel_operation_forbidden`, aunque los actores anteriores hayan terminado. |
| Retención ante inputs rechazados antes del nacimiento | **Minor · B-U1-03** | `scripts/eval/benchmark_process.py:370`, `:372` | Un `config` cabe individualmente en `MAX_REQUEST`, pero el gate completo, al añadir handler y envoltorio, lo supera. `_BirthRecord` ya está insertado en `_QUARANTINE`; `encode()` falla fuera del `try` de limpieza. Cada intento retiene permanentemente el registro, el proceso lógico y su configuración, aunque no haya nacido ningún recurso nativo. |

Evidencia de entrega comprobada: **300 casos, 269 PASS, 1 FAIL y 30 ERROR de fixture**. Cobertura WHOLE actual, sin exclusiones: startup **100 %**, process **84,27746 %**, episode **86,94853 %**, coordinator **71,92623 %**; gate **FALSE**.

El EOF original continúa con causa desconocida. El caso diagnóstico posterior PASS no demuestra H1 ni invalida el fallo original. Los defectos anteriores son deducciones del flujo actual, sin reproducción ejecutada por este reviewer; U2–U4 quedan fuera de esta revisión.

## Lente D

**1 hallazgo Important; 0 Critical; 0 Minor.** Evidencia estática sobre el diff compuesto U1; sin ejecutar pruebas ni procesos nativos.

| Criterio | Resultado | Fichero:línea y escenario |
|---|---|---|
| N+1 | Sin hallazgos | No aparecen consultas a BD en los cambios. |
| Bloqueos síncronos introducidos | Sin hallazgos | `benchmark_process.py:910`: el `sleep(0.001)` señalado por el selector ya existía; ahora la limpieza se ejecuta en un actor retenido. |
| Trabajo repetido | Sin hallazgos adicionales | No se acredita una degradación material por repetición de cálculos. |
| Crecimiento con el volumen | **Important — D-U1-01** | [benchmark_process.py:134](scripts/eval/benchmark_process.py:134): acumulación permanente de actores completados durante la vida del worker. |

**D-U1-01 — La custodia acumula también operaciones terminadas.** Cada `_NativeAction` se añade a `record.actors`, conserva `action`, `value`, `Event` y `Thread`, y permanece en la lista después del `join` satisfactorio. No existe eliminación de actores completados ni liberación de sus closures/resultados.

Escenario concreto: un sensor persistente a la cadencia predeterminada de **1 muestra/s durante una hora** realiza 3.600 llamadas normales. Las tres acciones nuevas por llamada —dos comprobaciones de ownership y una escritura— dejan **10.800 actores completados retenidos**, además del arranque. La memoria auxiliar crece **O(n)** aunque no haya operaciones pendientes; también quedan retenidos los bytes de las solicitudes por sus closures. En el canal canónico, cada llamada conserva además su resultado mediante `self.value` ([benchmark_process.py:138](scripts/eval/benchmark_process.py:138)).

Corrección propuesta: retirar los actores después de acreditar su terminación y `join`, manteniendo la custodia fuerte de los pendientes. El número de objetos se deduce del código; **no he medido RSS ni latencia**.

Los seis hashes coinciden con el freeze. La cobertura oficial actual confirma **100 / 84,27746 / 86,94853 / 71,92623 %**, sin exclusiones: el gate sigue fallando por coordinador. La baseline fallida y el EOF de causa desconocida permanecen sin resolver; este hallazgo no atribuye su causa ni acredita aceptación de U1.

