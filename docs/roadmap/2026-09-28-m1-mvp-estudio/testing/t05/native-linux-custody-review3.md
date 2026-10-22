# Revisión de dos lentes — intento 3: custodia Linux

**0 Critical · 0 Important · 0 Minor.** B03 corregido; se conservan los intentos anteriores y sus evidencias. La aceptación técnica depende de la QA independiente de 68 casos; T05 permanece abierta.

## Lente A

**Lente A · revisión 3: 0 Critical / 0 Important / 0 Minor.** Sin nuevos defectos de requisitos o constitución en el diff acotado de custodia Linux. Esto no cierra T-05.

| Tarea → criterio de aceptación | Resultado | Evidencia |
|---|---|---|
| T-05 → audio-post/FFmpeg Linux, traslado atómico, assets y manifiesto | ✗ Pendiente, correctamente declarado | `tasks.md:211`; esta unidad no implementa la publicación |
| T-05 → take ready, song.json y análisis beats | ✗ Pendiente, correctamente declarado | `tasks.md:212` |
| T-05 → limpieza propia del intento y failed/code | ✗ Pendiente, correctamente declarado | `tasks.md:213` |

Los criterios pendientes **no son gaps de esta entrega parcial**: T-05 permanece `en-progreso` (`tasks.md:198`).

| Criterio de revisión | Resultado y evidencia |
|---|---|
| Implementación y alcance | ✓ Los dos archivos modificados pertenecen a `worker/` y tests declarados (`tasks.md:202`). La custodia nativa está prevista en `improvement-plan.md:64` y ADR-0057. Fixture sin cambios. |
| B03: ENFILE después de TERM | ✓ `custody_linux_supervisor.py:117` contiene fallos de creación/register/select/close; continúa KILL y waits (`:277`, `:290`). Regresión en `test_worker_native_linux_custody.py:642`, con assertions **antes** del rescate (`:706`). |
| Consulta PGID fallida | ✓ Marca incertidumbre, evita señales de grupo y utiliza pidfds propios (`custody_linux_supervisor.py:258`, `:284`). Test exige testigo ajeno vivo y `confirmed=false` (`test_worker_native_linux_custody.py:806`). |
| Notificación final fallida | ✓ Defensa en `custody_linux_supervisor.py:110`; el padre conserva UNKNOWN sin evento final. Regresión en `test_worker_native_linux_custody.py:729`. |
| Tests y TDD | ✓ RED originales con argv/UTC/exit1 y fallos conductuales comprobados. Los errores de seams están separados. JUnit actual: **32 Linux + 36 Windows = 68 PASS**, cero fallos/errores/skips. Inyecciones controladas sobre procesos nativos; no agotamiento natural del sistema. |
| Cobertura oficial actual | ✓ JSON original: fachada **258/293 = 88,0546 %**, Linux **279/333 = 83,7838 %**, supervisor **264/327 = 80,7339 %**; líneas+ramas, cada módulo completo, cero exclusiones. |
| Constitución explícita | ✓ Sin violaciones observadas de arquitectura/autoridad server (`CONSTITUTION.md:31–35`), deserialización (`:41`), ledger/verificación (`:58`) o contratos (`:62`). |
| Verificación de tareas cerradas | ✓ No hay tarea cerrada en este diff. Las verificaciones completas de T-05 (`tasks.md:206`) siguen pendientes; no las ejecuté ni las doy por acreditadas. Evidencia parcial registrada en `tasks.md:1519–1523`. |
| Generados y documentación E2/E3 | N/a: el diff no toca `commands/`, `agents/` ni `hooks/`, ni modifica contratos públicos. No corresponde ejecutar export-interop. |

**Comprobaciones propias de solo lectura:** fuentes congeladas y 20 fuentes/copias actuales sin diferencias; 67 trazas originales y copias coincidentes; JUnit, comandos y cobertura original contrastados con los tests leídos.

**B03 anterior: corregido en esta unidad.** B01/B02 mantienen sus regresiones. Se conserva el contador 3; falta QA independiente fresca de los 68 casos y cobertura actual antes de aceptación por root. CPU2, audio, SQLite, publicación, E2E y T-05 completo siguen pendientes.

## Lente B

**Sin defectos de corrección nuevos.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| B03: fallo del selector después de TERM | ✓ Corregido: continúa SIGKILL, contención por pidfd y waits; conserva UNKNOWN. | `custody_linux_supervisor.py:117`, `:278`, `:303` |
| Consulta PGID fallida | ✓ Desautoriza señales de grupo; usa referencias propias y no confirma recursos. | `custody_linux_supervisor.py:259`, `:284` |
| Error secundario de notificación final | ✓ No interrumpe la finalización; sin evento final el consumidor conserva UNKNOWN. | `custody_linux_supervisor.py:110`, `custody_linux.py:286` |
| Regresiones B01/B02 | ✓ Preservadas las pruebas de constructor parcial y journal ENOSPC/EIO. | `test_worker_native_linux_custody.py:458`, `:568` |
| Evidencia vigente | ✓ Fuentes OWNED3 coinciden con el freeze; 67 RAW verificados por SHA. JUnit actual: Linux32 + Windows36, sin fallos, errores ni skips. | FINAL05, UUID `a186ab8b-5f11-4525-8886-5704d9395260` |

Cobertura recalculada desde el JSON oficial completo: **258/293, 279/333 y 264/327**, cada módulo ≥80 %, cero exclusiones.

B03 queda corregido según fuente y evidencia nativa archivada con errores controlados. Esta revisión fue exclusivamente de lectura: **no ejecuté pruebas nativas ni suites**. Se conserva review3 sin reiniciar el contador; la QA independiente y la aceptación completa de T05 siguen pendientes.

## Lente C

**Sin hallazgos de seguridad introducidos o reabiertos.** Gaps: **0 Critical · 0 Important · 0 Minor**.

Alcance: diff completo de los dos ficheros en `scope.diff`, contrastado con las fuentes actuales y su freeze SHA-256, estable al terminar. El selector automático no activó C; root la añadió por la autoridad sobre PGID/pidfd/FD durante la limpieza.

| Criterio | Resultado | Evidencia (`fichero:línea`) |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin hallazgos; el diff no incorpora ejecución construida desde entradas | `custody_linux_supervisor.py:117` |
| Autenticación y sesión | ✓ Sin cambios en sus controles | `custody_linux_supervisor.py:110` |
| Secretos hardcodeados | ✓ No añadidos | `test_worker_native_linux_custody.py:650` |
| Deserialización insegura | ✓ No introduce deserializadores ejecutables | `custody_linux_supervisor.py:113` |
| Path traversal / SSRF | ✓ No introduce destinos ni resolución de rutas desde entradas nuevas | `custody_linux_supervisor.py:97` |
| Permisos y autoridad de señalización | ✓ Una consulta PGID fallida desautoriza señales de grupo; fallback exclusivamente mediante referencias propias | `custody_linux_supervisor.py:259`, `:284` |
| Fallos durante limpieza | ✓ El selector auxiliar fallido conserva incertidumbre y permite continuar KILL y waits | `custody_linux_supervisor.py:117`, `:278`, `:303` |
| Confirmación y devolución de recursos | ✓ Sin confirmación cuando existe incertidumbre; perder la notificación final mantiene UNKNOWN en el consumidor | `custody_linux_supervisor.py:308`; `test_worker_native_linux_custody.py:782` |

**B03 anterior: corregido en el alcance revisado.** Los cuatro RED originales muestran descendientes vivos tras TERM real y ENFILE controlado. Los artefactos FINAL05 acreditan su terminación antes del rescate, waits propios, testigo ajeno vivo y `confirmed=false`. Las pruebas auxiliares de PGID y notificación final conservan UNKNOWN.

Verificación documental independiente: JUnit Linux **32** + Windows **36**, sin fallos/errores/skips; **67 RAW** actuales y copias con hashes coincidentes. Cobertura completa de líneas+ramas: fachada **258/293**, Linux **279/333**, supervisor **264/327**, cada fichero ≥80 %, cero exclusiones.

Revisión estática y lectura de evidencia existente; no ejecuté procesos nativos ni suites. Los fallos OS están inyectados sobre procesos reales y una fixture fija confiada. Root conserva pendiente la QA independiente de los 68 casos y la aceptación funcional completa de T-05.

## Lente D

**Sin hallazgos de rendimiento.** Critical: 0 · Important: 0 · Minor: 0.

Alcance: diff capturado en `inspection3/scope.diff`, dos ficheros; fuentes actuales coinciden con los tres SHA-256 del freeze. Activadores: rutas `worker` y `sleep-bloqueante` en línea 129.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| N+1 | `custody_linux_supervisor.py:266` | Sin consultas a BD; recorrido de referencias propias limitado a líder y descendiente registrado. |
| Bloqueos síncronos | `custody_linux_supervisor.py:117` | Fallback de ≤5 ms por fallo del selector, dentro de un proceso supervisor separado. No bloquea el event loop del server. |
| Trabajo repetido | `custody_linux_supervisor.py:303` | Conserva el patrón previo de espera; no añade serialización ni E/S de disco por iteración. |
| Complejidad con volumen | `custody_linux_supervisor.py:290` | Limpieza acotada por plazo previo de 5 s y referencias propias; no escala con canciones, takes o biblioteca. |
| Nuevos tests | `test_worker_native_linux_custody.py:641` | Seis casos adicionales de alcance fijo; sin degradación creciente con datos del dominio. |

**B03:** corregido según código y artefactos FINAL05: las cuatro variantes de fallo del selector continúan KILL/waits, ambos procesos propios salen antes del rescate, el testigo ajeno sobrevive y `confirmed=false`.

Evidencia revisada, sin ejecutar suites: JUnit Linux32 + Windows36 sin fallos; cobertura oficial actual 258/293, 279/333 y 264/327, cada fuente >80 % y cero exclusiones; hashes RAW coincidentes. Esto no constituye QA independiente ni aceptación completa de T05.

