> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

Resultado: BASELINE_PASS. Una baseline independiente: Linux42 + Windows46 = 88 casos, sin reducir selección ni repetir casos.

UUID: 6ff3aa28-f208-4cfd-a933-ad14b04b9854. Full real observado 3 veces. JUnit, RAW parent/child y coverage JSON actuales en final/. Copias RAW verificadas antes de combine --keep; sin datos históricos.

Cobertura oficial de los cuatro módulos WHOLE (líneas y ramas, cero exclusiones):
- apps\server\app\worker\custody.py: 88.17568 %.
- apps\server\app\worker\custody_linux.py: 86.78679 %.
- apps\server\app\worker\custody_linux_supervisor.py: 81.65138 %.
- apps\server\app\worker\custody_windows.py: 88.18898 %.

Gate por módulo: True. Ruff check exit 0; format --check exit 1.

Host-before: 10372 archivos físicos actuales del intérprete/base/venv antes de ejecución Python; alias Win32 por handle antes de casos. Source-before/after exacto: True; AST exacto: True. Ownership [].

Contenedor propio db1e1159a358b3250f419a9b528a2d95578dd03e96f62752ef222459c7885207 registrado antes de start, inspect/removal/gone registrados; gone: True.

Observaciones de casos en native-case-outcomes.json; evidencia real de kernel limitada al fixture confiado. CLOSED válido por deadline conserva su diferencia frente a UNKNOWN por transporte malformado. No se concede resource_returned por Job vacío ni por logs.

Limitaciones:
- Linux pinned base image interpreter/stdlib/libc, kernel and Docker daemon are unobserved base-image TCB; not physically copied out before subprocess start.
- Transient/unloaded import closure UNKNOWN; no universal resource closure, foreign-holder census or scheduler guarantee.
- Host files copied before Python launch; native final-handle alias resolution verified by bootstrap before case launch. Source/provider copies are hashed before imports; source alias final-handle resolution before Linux launch not separately captured.
- Initial bootstrap compared historical preimage fixture; failed before collection, preserved in bootstrap-history1. First Start-Process ExitCode null remains UNKNOWN; not reconstructed.
- Bootstrap repair success was directly observed via shell LASTEXITCODE=0; complete standalone PID/wait/UTC command receipt for that repair unavailable.
- Fixture teardown observations may be post-event; embedded birth/journal/witness records retain actual timestamps, no retrospective event timing inferred.
- Windows selected tests execute current checkout with prior physical copies; Linux executes fresh bind-mounted source/tools. Test AST, decorators, params, assertions and timeouts unchanged.
- No performance benchmark, task/roadmap/quality/GPU/E2E acceptance. Root adjudicates.

Sin cambios de código/tests/docs/ledger/Git. Modelo, tokens, EUR y horas IA NULL. No aceptación de T05 ni del roadmap.
