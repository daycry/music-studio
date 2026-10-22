# QA independiente del componente de limpieza nativa T09

Estado: **SCOPEDPASS**. Inspection7 / componente QA1; integración formal next4 separada y pendiente. Aceptación exclusiva ROOT, ninguna tarea cerrada.

Ejecución actual única: 253 tests, 0 failures, 0 errors, 0 skipped; 13 deselected. Exit 0. Argv y entorno originales: baseline-current/launch.json; UTC/exits: completion.json; stdout/stderr/JUnit originales en baseline-current. Selector completo y exclusiones exactas en selection.json. No suite repetida ni modificación de tests. El bootstrap y las trazas se copiaron/adaptaron del patrón final-baseline3 hacia esta carpeta privada; no se ejecutaron sus helpers históricos.

| WHOLE actual | Líneas | Ramas | Oficial líneas+ramas | Excluidas |
|---|---:|---:|---:|---:|
| scripts\eval\benchmark_canonical_runtime.py | 652/736 | 182/250 | 84.58418% | 0 |
| scripts\eval\benchmark_process.py | 400/462 | 134/190 | 81.90184% | 0 |

Coverage.py oficial usa exclusivamente padre e hijos NATIVOS de este único run: same-run-traces.json, bases originales coverage-native y .coverage.parent preservadas, agregado .coverage.aggregate y JSON oficial. Bases individuales no persistidas: 2, su ejecución/cobertura individual sigue UNKNOWN; detalle en native-unpersisted-coverage.json, no fabricación ni unión histórica. El checkpoint privado mantiene el patrón corregido _sealed_factory/reply; no instrumenta _signed/_write/_read.

255 nacimientos propios: disposiciones {'CLOSED_CONFIRMED': 232, 'UNKNOWN_QUARANTINED': 23}. native-ownership-cleanup.json conserva por nacimiento test, argv, configuración y gate previos, PID, FILETIME/Job según recibo real, limpieza/exit/hilos, o UNKNOWN si ausentes. Eventos recibidos/rechazados están en events.json. stderr hijo DEVNULL indisponible; no copia completa del RPC prometida. CloseHandle individual de eventos ejecutado por tests sin instrumentación externa individual. Threads finales en threads-final.json.

Las cuatro variantes reales de error autenticado comprueban revocación antes del wake, conservación del error/progreso/partial_raw, rechazo de tails, lectura vacía real de la tubería y cleanup repetido/concurrente. Seis variantes MAC/replay/binding/quota/lane/malformed conservan UNKNOWN_QUARANTINED pese a Jobempty. El retorno readline vacío observado no acredita physicalReadFile_zero_bytes_BLOCKED: sigue UNTESTED. Close desde el propio hilo lector sigue UNTESTED. Nada acredita scheduling universal, SLA, 160 jobs, calibración, hardware/material o cadencia.

Custodia antes/después: 78 fuentes/config/tests/runner con copias previas al primer test, 17002 originales históricos y 66 protegidos root. SHA protegido ec70abecbd64a7d50dc303a74f9c6a359cca97bb74ac47c31b393bf5961032c1; paths ['scripts\\eval\\tests\\test_benchmark_canonical_runtime.py']. Discrepancias: []. AST de tests originales congelado y cotejado antes/después. Inspección fuente3 actual cotejada antes. NONCLI completo en non-cli-inventory.json, excluye sólo cuatro top-level reservados y sí mismo.

Sin UI en este componente por diseño (test-plan: n/a (sin UI)). Ledger-lint/coverage-check ejecutados al cierre de esta comprobación acotada, no en P1: outputs originales en gates.json y archivos stdout/stderr separados. La puerta coverage-check acepta marcador, no acredita cobertura E2E; su lista de eximidos y avisos se conserva íntegra abajo. qa-gate E2E no ejecutado, sin results.json/UI fabricados. Gate acotado: pytest exit0, WHOLE cada módulo>=80, cero excluidas, custodia exacta. No GPU/PDH/Docker/WSL/Ollama/red externa/modelos/instalación. Los fixtures CPU de integración usan sockets loopback propios reales; las dos familias socket no autorizadas siguen excluidas exactamente en selection.json. No docs/ledger/Git/meter/aceptación/knowledge modificados. Modelo/tokens/EUR/horas IA reales NULL.

## Puertas deterministas originales
```
⚠️  T-09: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-10: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-11: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-12: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-13: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-16: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-20: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
ledger-lint: 0 incoherencias · 7 avisos (tasks.md)

ℹ️  test-plan: n/a (sin UI) declarado en improvement-plan.md: iniciativa sin UI por diseño, la puerta de cobertura NO se ha ejecutado (no es «cobertura OK»)
ℹ️  se listan para la revisión 21 tarea(s) del ledger (la spec no aporta criterios rastreables) (T-00, T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10, T-11, T-12, T-13, T-14, T-15, T-16, T-17, T-18, T-19, T-20): la puerta no exigía cobertura de estos (solo la exige de los [GWT]), así que aquí no se exime nada — su evidencia es el campo `Verificación` de la tarea que los cierra en tasks.md
⚠️  hay 17 ruta(s) con pinta de interfaz (apps/web/app/create/page.tsx [diff], apps/web/app/layout.test.tsx [diff], apps/web/app/layout.tsx [diff], apps/web/app/not-found.test.tsx [diff], apps/web/app/not-found.tsx [diff]…) y el plan declara «test-plan: n/a (sin UI)»: o el marcador sobra, o esas rutas no son UI — dilo en el ledger antes de que la revisión lo pregunte ([diff] = fichero cambiado, [ledger] = campo `Archivos`)
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19", "T-20"], "eximidos_exigidos": false, "rutas_ui": ["apps/web/app/create/page.tsx", "apps/web/app/layout.test.tsx", "apps/web/app/layout.tsx", "apps/web/app/not-found.test.tsx", "apps/web/app/not-found.tsx", "apps/web/app/page.tsx", "apps/web/app/pages.test.tsx", "apps/web/app/songs/page.tsx", "apps/web/app/system/page.tsx", "apps/web/components/PlayerDock.test.tsx", "apps/web/components/PlayerDock.tsx", "apps/web/components/StudioShell.test.tsx", "apps/web/components/StudioShell.tsx", "apps/web/components/ThemeProvider.test.tsx", "apps/web/components/ThemeProvider.tsx", "apps/web/styles/globals.css", "apps/web/styles/tokens.css"], "rutas_ui_origen": {"apps/web/app/create/page.tsx": "diff", "apps/web/app/layout.test.tsx": "diff", "apps/web/app/layout.tsx": "diff", "apps/web/app/not-found.test.tsx": "diff", "apps/web/app/not-found.tsx": "diff", "apps/web/app/page.tsx": "diff", "apps/web/app/pages.test.tsx": "diff", "apps/web/app/songs/page.tsx": "diff", "apps/web/app/system/page.tsx": "diff", "apps/web/components/PlayerDock.test.tsx": "diff", "apps/web/components/PlayerDock.tsx": "diff", "apps/web/components/StudioShell.test.tsx": "diff", "apps/web/components/StudioShell.tsx": "diff", "apps/web/components/ThemeProvider.test.tsx": "diff", "apps/web/components/ThemeProvider.tsx": "diff", "apps/web/styles/globals.css": "diff", "apps/web/styles/tokens.css": "diff"}, "rutas_ui_degradado": null}

```

Pendientes: physical ReadFile bloqueado, close desde lector, integración formal next4, matriz completa T09/calibración y restantes criterios del ledger. Sin handoff documenter ni estados cerrados.

Aviso global documental: coverage-check detecta 17 rutas UI del diff compartido de M1, ajenas al componente M0/T09 auditado. No se modifica el marcador/test-plan; root adjudica el aviso en el ledger. Este SCOPEDPASS no es QA global del checkout. Las puertas documentales se ejecutaron al cierre, no en P1.

Despacho mediante Agent nativo del orquestador, sin CLI propia ni metadata de actor fabricada. Los originales del run pytest y recibos nativos sí están conservados.
