> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Corrección nativa acotada: fase 4

Estado: SCOPED_FIX_WITH_CONCERNS. Unidad revisable, sin aceptación; revisión independiente fresca seguida de QA corresponde a ROOT. No reinicio de contadores ni cierre de T09.

## Causa y cambio

La causa original probada permanece en prior-originals/report.md, causal-witnesses.json y native-ownership-cleanup.json: un error autenticado seguido por otro terminal válido en MAC provoca rechazo lógico; antes del fix ese rechazo detenía el único observador de EOF. El Job vacío y el lector terminado no justificaban retorno conocido.

ParentMux valida autenticación, binding, secuencia, tipo y cuota antes de admitir el error. En el mismo lock de control, antes de publicar en la cola, congela los bytes del error, revoca live, conserva WorkerFailure y autoriza únicamente esa transición privada de lectura. Ningún JSON/booleano del caller otorga autoridad. No se admiten resultados/progresos posteriores; tampoco tras un fallo previo. OwnedProcess conserva la primera razón de rechazo mientras continúa leyendo la tubería física revocada. Sólo el retorno vacío real de readline marca reader_eof. Nunca Jobempty, poll ni salida del hilo.

El drain tiene tope de 66 frames y 17301570 bytes, un solo frame de memoria más el terminal congelado, y deadline mínimo entre el original y 220ms desde la revocación. No se añaden sleeps ni presupuestos. El cleanup existente termina sólo su Job original. El cierre concurrente conserva una sola reclamación y recibo; el lector no espera ni se une a sí mismo, y un cleanup sin lector unido queda UNKNOWN. No extracción de módulos ni exclusiones.

## TDD y validación

RED original: nodeid protegido error-native_protocol_error, pytest exit1, aserción resources_returned falsa, antes de modificar producción (2026-10-08T05:18:02.569687+00:00). RED nuevo: test_authenticated_error_rejects_tail_and_reads_real_eof[False-2], exit1, WorkerFailure era stale_or_reordered_reply en vez de native_protocol_error (2026-10-08T05:19:00.943491+00:00). No son fallos de imports/colección/API ausente. Copias exactas de source/test/runner/config/bootstrap/gate antes de cada nacimiento disponibles por run/source-before y births/*/before.json.

Mínimo GREEN nuevo y original: exit0; diez regresiones nativas: exit0. Cuatro variantes prueban error admitido con result posterior rechazado, progreso posterior rechazado, revocación antes del wake y cierre concurrente; seis prueban preterminal malformed/MAC/replay/quota/binding/lane UNKNOWN con Jobempty y sin lectura vacía. ReadObserver sólo delega a la tubería FileIO real y archiva en memoria los bytes retornados para las aserciones; no EOF artificial ni mocks de proceso/Job/evento. Los tests conservan error original, progreso/partial_raw y mismo recibo tras close repetido. Son observaciones de estas trayectorias y scheduling, no garantía de tiempo real bajo todo scheduling.

Final-baseline3: 253 tests, 0 failures, 0 errors, 0 skips; exit 0. Selector exacto en selection.json: process/canonicalruntime/nuevo módulo/integración y vecinos apropiados; EXCLUYE test_real_native_raw_before_later_block, coordinador no relacionado y dos familias de pruebas socket no autorizadas. No suites completas ajenas. Ruff y formato static2 exit0. TDD n/a: informes/config/bootstrap estáticos; se conserva su historial.

## Cobertura oficial vigente

| WHOLE producción | Líneas | Ramas | Oficial líneas+ramas | Excluidas |
|---|---:|---:|---:|---:|
| scripts\eval\benchmark_canonical_runtime.py | 651/736 | 181/250 | 84.38134% | 0 |
| scripts\eval\benchmark_process.py | 400/462 | 134/190 | 81.90184% | 0 |

Un único run final-baseline3, fuentes congeladas actuales y 253 trazas UUID nativas más padre. Base .coverage.aggregate, JSON oficial, originales por hijo y JSON individuales están archivados; todas las bases del mismo run se enumeran explícitamente, sin unión histórica ni promedios. Nacimientos sin base persistida: ['571f0ffe2d1649d4b3fbd9ac22c2820b', 'f79c24049f88496c9617b81d2162e1ae']; su cobertura individual es UNKNOWN, no se sintetiza ni se excluyen trazas existentes. Detalle real por testcase/Popen/asignación/cleanup en native-unpersisted-coverage.json. Corresponden a failed_assignment_never_opens_handler_gate y startup_block_bounded: no se infiere ni fabrica cuánto ejecutaron antes de morir. Todas las bases de los hijos nuevos de regresión están persistidas en este run. La cobertura child canonicalruntime es real; revisar per-child-summary.json. Las cifras de líneas y ramas individuales se muestran separadas; el gate WHOLE usa la métrica combinada oficial.

## Custodia

68 fuentes iniciales, dos módulos cambiados y un test nuevo. Root protege 66 fuentes ajenas, parity True; tests previos byte/AST exactos, incluido SHA ec70abecbd64a7d50dc303a74f9c6a359cca97bb74ac47c31b393bf5961032c1. La custodia del diagnóstico previo verifica 542 archivos, mismatches []; su conjunto inicial de 68 fuentes incluye los dos módulos ahora autorizados. No extrapolación global fuera de esos manifiestos.

Nacimientos final actuales: 255, CLOSED_CONFIRMED 232, UNKNOWN_QUARANTINED 23, cleanup ausente 0. PID, FILETIME, asignación y recibo real por nacimiento en native-ownership-cleanup.json. Los cierres individuales de eventos nativos no están instrumentados: el test ejecuta CloseHandle en finally; hecho individual externo UNKNOWN. stderr original DEVNULL indisponible, no datos inventados. Eventos/frame recibidos y rechazos se guardan por run, no se afirma copia íntegra del RPC original. Los casos deliberados UNKNOWN mantienen cuarentena. Threads finales reales por run en threads-final.json.

La aceptación anterior de cinco fuentes 80.52–86.51 era limitada. Con canonicalruntime modificado, esa ejecución es evidencia histórica de dependencia; no un freeze actual ni una aceptación renovada de los cinco módulos. Fuente actual exacta del run: True. CLI originales reservados intactos; inventario NONCLI excluye sólo esos cuatro nombres en el nivel superior y su propio fichero.

## Incidentes y límites

final-baseline1 se conserva íntegro: 243PASS/10FAIL/13deselected. Los diez fallos son first.wait(1), antes de la trayectoria causal; retirar los checkpoints privados adicionales _signed/_write/_read y usar el patrón previo dio GREEN al nodeid exacto con cobertura, sin modificar producto/tests/presupuestos. El mecanismo interno de esa demora no se atribuye como causa probada; se registra el contraste observado. Final-baseline2: 253PASS/13deselected, pero 20 nacimientos carecían de base persistida, incluidos hijos nuevos; no se ocultó ni se aceptó ese agregado como final. Se añadieron checkpoints privados _sealed_factory/reply sólo en el scheduler; validación de diez regresiones guardó 20/20 bases de hijos. Final-baseline3 aporta exclusivamente la cobertura vigente, sin unión de esas ejecuciones. Ruff inicial y reparación del import de fixture propia/formato conservados. La primera lectura CONTINUE incluyó historial; no usado como estado actual. Un patch privado duplicado fue rechazado atómicamente; una consulta PowerShell falló por sintaxis de pipeline y se corrigió sin efectos.

Incidente de orden de bootstrap: static.ps1 inicial y primeras llamadas finish/deliver cargaron env.ps1 antes de fijar TEMP/UV privados; su consulta gestionada python --version ocurrió antes de esos overrides. Antes de Ruff/imports de helpers estaban fijados; no se observó escritura externa ni se hizo instalación. Todos los runs nativos usan run.ps1 con variables privadas antes y después del bootstrap. static.ps1 se corrigió y evidence.ps1 fija variables previamente para el cierre. No se retroperfecciona el orden inicial.

physicalReadFile_zero_bytes_BLOCKED sigue UNTESTED: lectura vacía observada no acredita ese bloqueo específico. El test nuevo ejercita caller/close concurrentes; no invoca directamente close desde el propio hilo lector: ese guard se revisa en código y no se reclama como rama nativa ejercitada. Sin GPU/PDH/WSL/Ollama/Docker/red/install/hostPython/globalcache/subagentes/goals/UI/E2E. No hardware/SLA/160/calibración/material/cadencia/liveCLI/fullT09 aceptados. Ledger/docs/decisiones/Git/acceptance/meter exclusivos ROOT. Modelo/tokens/EUR/horas IA reales NULL; allocation-root contiene sólo pesos estimados ajenos y no se altera. Contadores no reseteados. Revisión fresca y después QA ROOT pendientes.

Candidato para documenter/root, sin escribir docs/knowledge: síntoma UNKNOWN aun con Jobempty; causa rechazo lógico mata lector antes de EOF tras terminal autenticado; solución revocación confiable atómica separada del observador físico, limitada; evidencia RED original/nuevo y regresión native_error_cleanup de esta fase.
