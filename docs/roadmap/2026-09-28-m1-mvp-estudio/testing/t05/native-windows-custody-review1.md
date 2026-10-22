# Revisión de dos lentes — intento 1: custodia Windows

**0 Critical · 3 Important · 0 Minor.** Tres defectos de corrección pendientes, sin aceptación.

- **B-01** · apps/server/app/worker/custody.py:248: Second contain_unknown failure escapes finalizer; no receipt/done; wait can remain indefinite. Reviewer fresh in-memory injected backend reproduction; source control flow exact.
- **B-02** · apps/server/app/worker/custody.py:284: done is set before finalizer thread exits, join(0) can raise TimeoutError despite valid receipt. Source order and documented actual-thread scheduling window.
- **B-03** · apps/server/app/worker/custody_windows.py:407: OpenProcess handle lost if creation_time raises, or identity mismatch close fails before _own registers reference. Full member registration path and pre-registration failure branches inspected.

La evidencia de producción actual es final04; no se combinan corridas anteriores. Las pruebas de kernel reales y las inyecciones suplementarias se distinguen. Ruff declara E402 ignorado en bootstrap privado; no equivale a lint global.

## Lente A

**Lente A · revisión 1: 0 Critical, 0 Important, 0 Minor.** Sin defectos de requisitos o constitución identificados en la unidad acotada Windows. **Esto no acepta T-05 completa.**

Leídos los cuatro archivos completos y cotejados con `scope.diff`: 287/618/671/121 líneas, contenido idéntico y hashes actuales coincidentes con final04.

| T-05 → criterio de aceptación del ledger | Resultado | Evidencia |
|---|---|---|
| Ejecutar audio-post en Docker Linux, traslado atómico, assets y manifiesto | ✗ Pendiente; no declarado cumplido | `tasks.md:211`; esta entrega únicamente ejecuta la fixture benigna |
| Take ready, song.json y análisis beats dependiente | ✗ Pendiente; no declarado cumplido | `tasks.md:212`; no integración SQLite/runtime |
| Limpieza del intento propio y fallo tipado del take | ✗ Pendiente; no declarado cumplido | `tasks.md:213`; gate de staging inerte, `custody.py:1` |

Estos pendientes **no son gaps de esta unidad**: T-05 permanece `en-progreso` (`tasks.md:198`) y el plan contempla custodia antes de publicación/runtime (`improvement-plan.md:64`).

Las referencias de código siguientes pertenecen a `apps/server/app/worker/`; las de tests, a `apps/server/tests/test_worker_native_custody.py`.

| T-05 → criterio de la unidad Windows | Resultado | Código y test leído |
|---|---|---|
| Job propio, nacimiento suspendido, identidad y asignación antes de reanudar | ✓ | `custody_windows.py:233`, `:326`, `:442`; test `:145` |
| Herencia limitada y entorno/entrypoint internos | ✓ | `custody_windows.py:255`, `:336`; tests `:451`, `:582` |
| Registro del nieto, pertenencia y accounting; miembro desconocido impide cierre | ✓ | `custody_windows.py:425`, `:489`; tests `:145`, `:493`, `:600` |
| Reutilización de handles y escrow ajeno no autorizan destruir objetos extranjeros | ✓ | `custody_windows.py:168`, `:185`, `:549`; tests `:361`, `:379`, `:427` |
| Muerte real del padre termina hijo y nieto; testigo ajeno sobrevive | ✓ | Job kill-on-close `custody_windows.py:235`; test `:190` |
| Pipes acotadas, writer independiente, cancelación, waits y EOF antes del cierre completo | ✓ | `custody.py:71`, `:103`, `:206`; `custody_windows.py:571`, `:602`; test `:243` |
| Cancelación concurrente/coroutine conserva finalizador; join repetido | ✓ | `custody.py:262`, `:265`, `:280`; test `:304` |
| Transporte inválido conserva UNKNOWN y `resources_returned=false` | ✓ | `custody.py:162`, `:249`; test `:332` |

| Comprobación transversal | Resultado |
|---|---|
| Alcance y `Archivos` | ✓ Cuatro archivos, cero fuera de alcance; worker y tests corresponden a la secuencia aprobada. `tasks.md:204`, `:1207`; `improvement-plan.md:64`. |
| Tests y cobertura actual | ✓ final04: **31 passed**, exit 0, JUnit sin errores/fallos/skips. `custody.py`: **182/207 = 87,9227 %**; Windows: **331/362 = 91,4365 %**; cero exclusiones. |
| Procedencia de cobertura | ✓ Dos trazas originales de final04 con hashes comprobados; combinación oficial limitada a esa corrida. Padre efímero guarda antes de morir. Sin unión histórica ni cobertura atribuida al workload. |
| TDD | ✓ Originales conductuales RED con argv/UTC/exit y salidas conservadas. Bootstrap/imports no contabilizados como RED. Carencia histórica de recibos iniciales completos explícitamente reconocida. |
| Constitución explícita | ✓ Sin contradicción identificada con `docs/CONSTITUTION.md:18`, `:24`, `:25`, `:33`, `:35`, `:42`. |
| Verificación de tareas cerradas | ✓ No hay tarea cerrada en este diff. Las verificaciones completas de T-05 siguen pendientes; no se ejecutaron para suplir evidencia. `tasks.md:206`, `:1260`. |
| Generados/descriptores E2–E3 | N/A: el diff no toca `commands/`, `agents/` ni `hooks/`; no procede ejecutar export-interop. |

**Evidencia del productor inspeccionada, no suite reejecutada por el revisor.** Pruebas nativas separadas de inyecciones suplementarias. QA independiente, Linux, audio, CPU2, publicación, SQLite y E2E siguen pendientes. Ruff declarado usa `--ignore E402`; no acredita lint global sin excepciones.

## Lente B

Encontrados **3 defectos de corrección**; ninguno Critical.

| Criterio | Gravedad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| Finalización finita ante errores | Important | `apps/server/app/worker/custody.py:248`; `custody_windows.py:562` | Si el wait de contención lanza `OSError`, la segunda llamada a `contain_unknown()` escapa del manejador. El finalizador termina sin recibo y sin señalar `done`; `await owner.wait()` permanece esperando indefinidamente. **Reproducido en memoria con backend inyectado**, sin operaciones OS. |
| Sin carreras al entregar el recibo | Important | `apps/server/app/worker/custody.py:284` | El finalizador señala `done` antes de terminar su hilo. Si la coroutine despierta en ese intervalo, `join(0)` encuentra el hilo vivo y lanza `TimeoutError` pese a existir un recibo válido. **Evidencia estática** del orden de ejecución. |
| Retención de handles ante validación fallida | Important | `apps/server/app/worker/custody_windows.py:407` | Tras un `OpenProcess` exitoso, si `creation_time()` lanza `OSError`, el handle sale sin cierre ni registro. También se pierde su referencia si el cierre de la rama de identidad incorrecta falla. La cuarentena del grupo no conserva ese handle porque `_own()` todavía no se ejecutó. **Evidencia estática**. |

Cotejados los cuatro diffs completos con las fuentes congeladas de **final04**. Evidencia del productor verificada: **31 PASS**, cobertura completa **182/207** y **331/362**, cero exclusiones y dos trazas actuales con hashes coincidentes. No repetí la suite ni ejecuté pruebas nativas nuevas.

## Lente C

**Sin hallazgos de seguridad** en los cuatro archivos del diff congelado final04. Gaps: **Critical 0 · Important 0 · Minor 0**.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección de comandos/plantillas/SQL | ✓ Ejecutable y fixture internos fijados; argumentos con `list2cmdline`, sin shell ni SQL | `custody_windows.py:255`, `custody_windows.py:348` |
| Autenticación y sesión | ✓ Sin nuevas superficies de autenticación; transporte correlacionado mediante el protocolo existente | `custody.py:63`, `custody.py:173` |
| Secretos | ✓ Entorno limitado a cuatro variables permitidas; sin credenciales hardcodeadas | `custody_windows.py:287` |
| Deserialización insegura | ✓ Usa el decoder existente; valida estructura del handshake antes de registrar miembros | `custody.py:124`, `worker_custody_child.py:92` |
| Path traversal | ✓ Rutas resueltas dentro del proyecto y entrypoint fijo, con entradas internas confiables | `custody_windows.py:256`, `custody_windows.py:279` |
| SSRF | ✓ Sin operaciones de red introducidas | Los cuatro archivos completos |
| Permisos y autoridad sobre objetos | ✓ Herencia selectiva de tres handles; identidad, pertenencia y anclaje independiente antes de operar | `custody_windows.py:168`, `custody_windows.py:334`, `custody_windows.py:425`, `custody_windows.py:549` |
| Liberación incorrectamente acreditada | ✓ Fallos y miembros no registrados conservan UNKNOWN; devolución condicionada al cierre confirmado | `custody_windows.py:520`, `custody.py:249` |

**Evidencia:** revisión estática completa y cotejos de solo lectura ejecutados: diff idéntico a las cuatro fuentes actuales y hashes coincidentes con final04. JUnit del **productor**: 31 PASS; cobertura completa **182/207 (87,92 %)** y **331/362 (91,44 %)**, cero exclusiones; dos trazas originales con hashes coincidentes. No ejecuté tests ni probes nativos.

El selector automático no activó C; el root la añadió por sensibilidad de handles, entorno y custodia kernel. Resultado limitado a esta unidad con fixture benigno; no acredita integración de audio ni cierre de T05.

## Lente D

**Sin hallazgos de rendimiento.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| N+1 | `custody_windows.py:425` | Sin consultas SQL. Registro limitado al árbol benigno de esta unidad. |
| Bloqueos síncronos | `custody.py:108`, `custody.py:183`, `custody.py:283` | E/S y finalización en hilos propios; `await asyncio.sleep` cede el control. |
| Trabajo repetido evitable | `custody_windows.py:571`, `custody_windows.py:586` | Transporte por bloques de 4096 bytes; sin reserialización repetida del mensaje completo. |
| Crecimiento con volumen | `custody.py:75`, `custody.py:167` | Colas de capacidad 4 y retención de stdout/stderr limitada a 16 KiB por canal. |

Revisión estática del diff completo de cuatro fuentes, cuyos hashes coinciden con final04. Evidencia del productor cotejada: 31 PASS y cobertura completa por módulo 87,92 % / 91,44 %, sin exclusiones. No ejecuté suites ni pruebas nativas nuevas.

Conclusión limitada a la unidad Windows con fixture benigno; no acredita integración CPU2 ni audio.

