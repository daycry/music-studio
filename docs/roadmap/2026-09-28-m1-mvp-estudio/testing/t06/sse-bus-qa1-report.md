> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

QA_UNIT_PASS

Única baseline actual: pytest exit 0; JUnit {'cases': 453, 'failed': 0, 'skipped': 0, 'passed': 453}.

WHOLE apps/server/app/queue/events.py: 195/203 = 96.05911330%, excluidas 0.

WHOLE apps/server/app/sse.py: 202/208 = 97.11538462%, excluidas 0.

Fuentes causales protegidas exactas: True; tests seleccionados/helpers transitivos copiados byte exactos y AST preservada: True; runner/config/fixture exactos: True.

Ruff check exit 0; format --check exit 0.

Historia original intacta: 452 PASS/1 FAIL timeout801, causa UNKNOWN; diagnósticos 1/2 no explican la causa. Esta QA independiente no vuelve verde aquel resultado ni demuestra flakiness o causa de carga.

TDD histórico: seis RED conductuales U1 y RED2 canónico A01 cotejados con comandos/JUnit/preimagen. No se han escrito tests ni RED nuevos. TDD n/a runner y configuración privados.

SQLite real en fixtures privadas; bus con hilos/asyncio reales en proceso. Limpieza de descendientes OS UNKNOWN. No prueba custodia Windows/Linux, CPU2, HTTP, heartbeat efectivo 15s, snapshot/WAL reset, auth, Last-Event-ID, API, cliente, navegador o E2E. CA y T06/M1 abiertos; UI/E2E pendientes; Playwright n/a en esta unidad.

Ownership []; sin cambios producto/tests/ledger/docs/Git/meter. Cambios ajenos disjuntos worker/custodia no se usan como drift global. CLI exit desconocido hasta cierre del padre; exit pytest arriba real. Tokens/EUR/horas IA null.

Cotejo suplementario: tests seleccionados y helpers transitivos exactos True; protección causal exacta True; EventConsumer AST anterior intacta. Copias no seleccionadas son archivo, no freeze de worker/tests. Ledger lint exit 0: ledger-lint: 0 incoherencias · 0 avisos (tasks.md)


Corrección de clasificación privada: el comparador inicial amplio incluyó test_worker_native_custody.py, cambiado legítimamente por el actor disjunto. Se preservan initial-broad-scope-{receipt.json,report.md}; no es drift causal ni fallo de producto. Scope protegido y seleccionado sin cambios; freeze de revisión cuatro fuentes exacto. Baseline ejecutada una vez, sin rerun ni corrección de producto.
