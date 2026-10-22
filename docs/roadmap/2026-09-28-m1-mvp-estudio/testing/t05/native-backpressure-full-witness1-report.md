> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Entrega acotada: regresión de comportamiento de fixture Linux

La única ejecución con estímulo original pasó: 1 PASS, 0 FAIL/ERROR/SKIP, 3 excepciones Queue.Full reales, cola 4/4, UNKNOWN_QUARANTINED, transport_error, release_gate=false y Owner retenido. UTC del comprobante: 2026-10-09T03:17:52.925042+00:00.

El nombre físico red01 conserva la fase prevista; **su resultado fue PASS, no RED causal**. No hubo reintento, modificación de fixture ni GREEN posterior. Conforme a la instrucción explícita «If initialtest naturallyFull ... stopforRoot», se detuvo el rediseño. La causa histórica sigue UNPROVEN; este resultado no garantiza saturación bajo otros arranques/cargas ni refuta BP01 deadline-before-Full legítimamente CLOSED.

Cambio único: función nueva test_backpressure_fixture_really_saturates_queue añadida al fichero nativo Linux. Queue.put del objeto real se observa pasando todos los argumentos y propagando retornos/excepciones originales; no hay consumidor, capacidad artificial, cancelación, bloqueo del lector ni alteración de deadline0.25/join10. La primera aserción exige Full real; después exige UNKNOWN/no release/Owner retenido. Fixture, funciones/decoradores/params/asserts anteriores y 19 casos drain permanecen intactos; byte-prefix y AST originales cotejados. Producción y Windows protegidos exactos. No modificación del ledger/docs/ADRs/Git/medidores.

Evidencia: red01/inputs-before.json y source contienen copias físicas y SHA/bytes previos de fuentes, tests, fixtures, runner y dependencias existentes. red01/proof/backpressure-before-assertions.json contiene intentos, nacimientos reales, disposition/waits nativos y referencias fuertes post-join antes de aserciones. No se presenta una referencia legítimamente cerrada como observación viva pre-close; no se añadió witness independiente. red01/proof/actual-popen.json registra procesos reales; JUnit en red01/proof/junit.xml. No se instrumentaron retornos kernel ni se forzó True.

Docker propio fijado, CPU2, uid65532, cap-drop ALL, read-only, no-new-privileges, network none, pids128, memoria1GiB, tmpfs128m, sin GPU/pull/build/install. CID e56ebca8ee07872bd4cabdfcf01ee4a908c3d3caaa514c71bd3a2c4df21c8c80 registrado antes de start; procesos Docker esperados con Popen.wait directo, inspect tras ejecución, rm normal y posterior inspect exit1 confirman gone. Logs y argv/PID/UTC/exit separados en red01, sin sobrescribir fases previas. Hostload exclusivo y coste observador UNKNOWN; intérpretes/stdlib/kernel/libc declarados TCB, completitud transitoria de imports UNKNOWN.

No final Linux42+Windows46 ni revisión/QA independiente al haberse tomado la rama de parada inicial expresamente autorizada. Runtime coverage gate n/a: cero producción cambiada; no métricas nuevas ni unión con trazas históricas. Modelo/tokens/EUR/horasIA NULL sin originales proveedor. Persisten todos los gates y deudas históricos indicados por Root. La regresión está lista para revisión; no hay aceptación de componente/hito.

NEEDS_CONTEXT: el estímulo original produjo Full real en la única ejecución; Root debe resolver si procede el rediseño sin RED nuevo.
