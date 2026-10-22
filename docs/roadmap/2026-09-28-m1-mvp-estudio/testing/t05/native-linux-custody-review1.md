# Revisión de dos lentes — intento 1: custodia Linux

0 Critical · **2 Important** · 0 Minor. B-01 y B-02 requieren corrección y regresión nativa. T-05 continúa en progreso.

## Lente A

**Lente A — FINAL06: sin gaps de requisitos o constitución en la unidad acotada.** Critical: **0** · Important: **0** · Minor: **0**. Esto no cierra T-05 ni sustituye la QA independiente.

Revisé los cinco ficheros completos del diff, fuentes actuales, tests, fixture, contexto Windows, plan, brief y ledger. Comprobé **13/13 SHA de fuentes** y **49/49 trazas**; coinciden con la entrega congelada.

| Tarea → criterio general | Resultado | Evidencia |
|---|---|---|
| T-05 → audio-post/FFmpeg, traslado atómico, assets y manifiesto | ✗ Pendiente, correctamente declarado | [tasks.md:211](./docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:211). Esta unidad ejecuta una fixture fija. |
| T-05 → take `ready`, `song.json` y análisis beats | ✗ Pendiente, correctamente declarado | [tasks.md:212](./docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:212). No se atribuye publicación ni escritura SQL a la custodia. |
| T-05 → limpieza acreditada y fallo tipado del take | ✗ Pendiente, correctamente declarado | [tasks.md:213](./docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:213). El gate actual permanece separado de staging/runtime. |

Estos pendientes **no son gaps de esta entrega**: T-05 continúa `en-progreso`, con sus tres casillas abiertas.

| Criterio de revisión / unidad | Resultado | Evidencia fichero:línea |
|---|---|---|
| (1) Correspondencia entre implementación y estado declarado | ✓ | [tasks.md:198](./docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:198), [tasks.md:1459](./docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:1459): entrega técnica pendiente de revisión/QA, sin cierre funcional. |
| (2) Alcance y `Archivos` | ✓ | [tasks.md:204](./docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:204), [improvement-plan.md:64](./docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md:64): custodia nativa prevista; tres módulos dentro de `worker/` y dos ficheros de tests. |
| Nacimiento controlado y supervisor fuera del PGID | ✓ | [custody_linux_supervisor.py:48](./apps/server/app/worker/custody_linux_supervisor.py:48), [test_worker_native_linux_custody.py:124](./apps/server/tests/test_worker_native_linux_custody.py:124). |
| TERM/KILL, líder retenido y espera de descendientes | ✓ | [custody_linux_supervisor.py:203](./apps/server/app/worker/custody_linux_supervisor.py:203), [test_worker_native_linux_custody.py:102](./apps/server/tests/test_worker_native_linux_custody.py:102). |
| Muerte real del padre y supervivencia del testigo ajeno | ✓ | [test_worker_native_linux_custody.py:230](./apps/server/tests/test_worker_native_linux_custody.py:230): pidfds, EOF, espera y testigo comprobados por assertions explícitas. |
| Referencias ajenas/reutilizadas no autorizan señalización o cierre | ✓ | [custody_linux_supervisor.py:186](./apps/server/app/worker/custody_linux_supervisor.py:186), [test_worker_native_linux_custody.py:348](./apps/server/tests/test_worker_native_linux_custody.py:348), [test_worker_native_linux_custody.py:369](./apps/server/tests/test_worker_native_linux_custody.py:369). |
| Transporte acotado, cancelación y UNKNOWN conservador | ✓ | [custody_linux.py:207](./apps/server/app/worker/custody_linux.py:207), [test_worker_native_linux_custody.py:142](./apps/server/tests/test_worker_native_linux_custody.py:142), [test_worker_native_linux_custody.py:154](./apps/server/tests/test_worker_native_linux_custody.py:154). |
| (3) Tests y cobertura actual | ✓ | FINAL06: Linux **23 PASS**, Windows **36 PASS**, ambos exit **0**, sin errores ni skips. Cobertura WHOLE individual: `custody.py` **200/221 = 90,4977 %**; Linux **211/234 = 90,1709 %**; supervisor **173/202 = 85,6436 %**; **0 exclusiones**. |
| (4) Constitución explícita | ✓ | Sin violación introducida en el alcance revisado. Se conservan las fronteras del server/BD y contratos públicos ([CONSTITUTION.md:32](./docs/CONSTITUTION.md:32), [CONSTITUTION.md:62](./docs/CONSTITUTION.md:62)); tampoco se declara un cierre sin verificación ([CONSTITUTION.md:58](./docs/CONSTITUTION.md:58)). |
| (5) Verificación de tareas cerradas | N/A | Esta unidad no cierra ninguna tarea. Las dos verificaciones generales de [tasks.md:206](./docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:206) siguen pendientes; no las ejecuté para completar evidencia. |
| (6) Generados E2 y documentación E3 | N/A / ✓ | El diff no toca `commands/`, `agents/` ni `hooks/`: interop no aplica. La implementación respeta ADR-0057 y su secuencia acotada, sin cambiar contratos públicos ni contradecir la documentación vigente. |

La cobertura procede únicamente del UUID **`d38d21ab-c89e-4cdb-86fb-d902e3032069`**, con pathmaps explícitos y `combine --keep` registrado en exit 0. Es apoyo a la lectura de los tests, no prueba de aceptación por sí sola.

Los cuatro RED archivados muestran fallos funcionales: nieto vivo, scope Windows en Linux, cierre positivo tras reutilización de stdio y señal al supervisor ajeno. Las inyecciones se mantienen distinguidas de fallos espontáneos. **No queda acreditado un RED independiente para cada caso nuevo**, ni metadatos individuales completos de todos los subprocess Linux; son límites declarados, sin ampliarlos retrospectivamente.

**Evidencia del revisor:** lectura y cotejos de hashes/JSON/JUnit. No ejecuté suites, procesos nativos, Docker ni señales.

## Lente B

**2 defectos Important; 0 Critical y 0 Minor.**

| Criterio | Gap | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| Contención ante fallo de arranque | B-01 · Important | [custody_linux.py:131](/./apps/server/app/worker/custody_linux.py:131) | Si `os.dup()` falla con `EMFILE` después de `Popen`, el constructor propaga la excepción sin contener el supervisor. `LINUX_GROUPS` conserva el objeto parcial, incluido el writer de liveness y el socket de control: no llega EOF y el supervisor puede permanecer hasta 3600 segundos con el líder bloqueado en el gate. El llamador no recibe un grupo construido que pueda finalizar. |
| Limpieza garantizada ante errores del supervisor | B-02 · Important | [custody_linux_supervisor.py:198](/./apps/server/app/worker/custody_linux_supervisor.py:198) | Si el journal falla con `ENOSPC`/`EIO` después de registrar el nieto, la excepción sale de `main()` antes de TERM/KILL y los waits. El líder recibe EOF del registry y sale; el nieto continúa en `signal.pause()`. `contain_unknown()` intenta comunicarse con el supervisor ya muerto y no termina ese descendiente, aunque conserva el gate cerrado. |

Evidencia de ambos gaps: análisis estático de las fuentes congeladas; no ejecuté procesos ni señales. Verificados los 13 SHA actuales y las 49 trazas de FINAL06. La cobertura oficial de cada módulo supera el 80 %, sin exclusiones; no acredita estos caminos de fallo.

## Lente C

**Sin hallazgos de seguridad introducidos o reabiertos** en los cinco ficheros del `scope.diff` congelado de FINAL06.

| Criterio | Resultado | Evidencia `fichero:línea` |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Lanzamiento con argv, intérprete y fixture internos fijos; sin shell ni ejecución de payload | `custody_linux.py:108`, `custody_linux_supervisor.py:62` |
| Autenticación y sesión | ✓ El diff no incorpora endpoints ni modifica controles de sesión | `custody.py:63` |
| Secretos hardcodeados | ✓ Entorno mínimo, sin credenciales introducidas | `custody_linux.py:109` |
| Deserialización insegura | ✓ JSON; sin pickle, eval ni reconstrucción ejecutable | `custody_linux.py:161`, `custody_linux_supervisor.py:183` |
| Path traversal y SSRF | ✓ Rutas del lanzamiento interno confiable; sin destino de red o ruta ejecutable recibidos del protocolo | `custody_linux.py:94`, `custody_linux_supervisor.py:62` |
| Autoridad sobre procesos | ✓ Candidatos ajenos permanecen fuera de `refs`; señalización por referencias aceptadas y PGID del líder retenido | `custody_linux_supervisor.py:185`, `custody_linux_supervisor.py:204`, `custody_linux_supervisor.py:225` |
| FD, herencia y liberación | ✓ Validación de referencias antes del cierre; incertidumbre impide liberar recursos; workload sin writer de liveness | `custody_linux.py:31`, `custody_linux.py:295`, `custody_linux_supervisor.py:55`, `custody.py:268` |

**Gaps:** Critical **0**, Important **0**, Minor **0**. Sin escenario de explotación concreto acreditado ni CWE que asignar.

Revisión estática y documental, estrictamente de solo lectura. Los 13 SHA actuales coinciden con la congelación. El JSON oficial muestra cobertura WHOLE de **200/221**, **211/234** y **173/202**, sin exclusiones. Las ejecuciones nativas pertenecen al productor; no ejecuté pruebas, señales ni procesos nativos, y este resultado no constituye aceptación de T05.

El selector automático dio C=false; root añadió esta lente por fork/exec, autoridad de señales, pidfd, reutilización de FD y herencia de liveness.

## Lente D

**Sin hallazgos de rendimiento.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Evidencia fichero:línea | Resultado |
|---|---|---|
| N+1 | `custody_linux.py:194`; `custody_linux_supervisor.py:178` | Sin consultas a BD; registro limitado al árbol fijo. |
| Bloqueos síncronos | `custody.py:323`; `custody_linux.py:235` | Join delegado mediante `asyncio.to_thread`; transporte no bloqueante con espera y cancelación. |
| Trabajo repetido evitable | `custody_linux.py:175`; `custody_linux_supervisor.py:232` | No se acredita degradación material dentro del alcance y volumen actuales. |
| Complejidad y volumen | `custody_linux.py:172`; `custody.py:86` | Control limitado a 8 eventos y colas de 4; sin crecimiento problemático identificado. |

Revisión estática del diff completo de cinco ficheros y fuentes actuales; SHA-256 coincidentes en las 13 fuentes declaradas. Lente activada por rutas `worker`, según `lens-selection.json`.

No ejecuté pruebas ni procesos nativos. Este resultado no constituye aceptación de T05 ni medición de rendimiento.

