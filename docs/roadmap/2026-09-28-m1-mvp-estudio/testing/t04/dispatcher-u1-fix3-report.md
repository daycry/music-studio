# T04 U1 fix3 — corrección acotada para revisión fresca y QA independiente

B3-01 y D3-01 corregidos únicamente en admission.py, dispatcher.py y test_dispatcher_scanning.py.

B3-01: PreclaimResolutionError conserva ResolutionError tipado; se emite sólo desde staging o recheck de inputs anterior a escribir job/intento. El scan automático continúa sólo tras ese rechazo. El job_id explícito propaga el error sin visitar el tail. No se reclasifican commit, probe ni cleanup: los fallos conocidos/desconocidos siguen failclosed y conservan staging/attempt. La reserva transaccional corta y su recibo no se rediseñan.

D3-01: una ocupación de screening por dispatch, compartida entre páginas y consultada con to_thread. Sólo sirve para descartar. El candidato seleccionado conserva resolve completo, identidad/health/VRAM frescos, _preflight y reserva con recheck vigente. Finite snapshot, páginas <=400, prioridad/FIFO UTC y los 39 casos anteriores permanecen exactos.

## Causa raíz y RED

Aislamiento: reserve elevaba errores de entrada antes del claim fuera de la captura del dispatcher; capturar ResolutionError completo habría tragado fallos after_commit. _screen repetía el mismo SELECT síncrono por candidato GPU elegible. Los RED nativos acotan ambas causas; no se atribuyen los fallos a catálogo ausente, schema o import.

RED: apps/server/tests/test_dispatcher_scanning.py::test_native_input_race_between_resolve_and_reserve[False-upload_deleted] falló con app.queue.inputs.ResolutionError: Input not owned · 2026-10-08T00:18:33.577016+00:00
RED: apps/server/tests/test_dispatcher_scanning.py::test_native_input_race_between_resolve_and_reserve[False-file_deleted] falló con app.queue.inputs.ResolutionError: Input file absent or outside data · 2026-10-08T00:18:41.891649+00:00
RED: apps/server/tests/test_dispatcher_scanning.py::test_native_input_race_between_resolve_and_reserve[False-file_changed] falló con app.queue.inputs.ResolutionError: Input changed during staging · 2026-10-08T00:18:44.934553+00:00
RED: apps/server/tests/test_dispatcher_scanning.py::test_native_durable_gpu_screen_once_per_dispatch_snapshot[200] falló con AssertionError: {'candidates': 200, 'database': 'native file SQLite head0005', 'adapter': 'synthetic Catalog', 'occupancy_selects': [200, 200], ...}
assert [200, 200] == [1, 1]
  
  At index 0 diff: 200 != 1
  Use -v to get more diff · 2026-10-08T00:18:48.007895+00:00
RED: apps/server/tests/test_dispatcher_scanning.py::test_native_durable_gpu_screen_once_per_dispatch_snapshot[400] falló con AssertionError: {'candidates': 400, 'database': 'native file SQLite head0005', 'adapter': 'synthetic Catalog', 'occupancy_selects': [400, 400], ...}
assert [400, 400] == [1, 1]
  
  At index 0 diff: 400 != 1
  Use -v to get more diff · 2026-10-08T00:19:02.967940+00:00
RED: apps/server/tests/test_dispatcher_scanning.py::test_native_durable_gpu_screen_once_per_dispatch_snapshot[2001] falló con AssertionError: {'candidates': 2001, 'database': 'native file SQLite head0005', 'adapter': 'synthetic Catalog', 'occupancy_selects': [2001, 2001], ...}
assert [2001, 2001] == [1, 1]
  
  At index 0 diff: 2001 != 1
  Use -v to get more diff · 2026-10-08T00:19:07.029121+00:00

## Verificación de esta corrección

Final dirigida y vecinos: **206 passed** = 125 previos + 39 scanning originales + 17 nuevos + 25 vecinos, una única corrida final sobre bytes actuales congelados. No se declara cumplida la verificación completa ni los CA de T04/U2/U3. El argv exacto y stdout/stderr están en final-current-frozen.command.json y sus .txt; JUnit único.

| Módulo completo | Cubiertas/total | % oficial | Excluidas |
|---|---:|---:|---:|
| apps/server/app/queue/dispatcher.py | 128/145 | 88.28 | 0 |
| apps/server/app/queue/admission.py | 192/203 | 94.58 | 0 |
| resolver.py, sin cambios, cualificado | 151/163 | 92.64 | 0 |

Datos oficiales .coverage y coverage-final.json conservados, cero exclusiones; sin unión de trazas históricas, changed-lines ni medias. Ruff check y format --check dirigidos: exit 0.

| Candidatos GPU | SELECT ocupación por despacho (dos snapshots) | SELECT en loop | Ticks heartbeat |
|---:|---|---:|---:|
| 200 | [1, 1] | 0 | 13 |
| 400 | [1, 1] | 0 | 18 |
| 2001 | [1, 1] | 0 | 44 |

SQLite nativo en fichero migrado a 0005, Admission/Resolver/Dispatcher públicos reales, engine disponible con adapter Catalog sintético y otro job GPU durable. El tail CPU se despacha; cero nuevas reservas GPU. Baseline RED: consultas [200,200], [400,400], [2001,2001]. Dos controles prueban ocupación nueva después de screening tanto ante preflight como ante reserva. Seis controles after_commit prueban errores ResolutionError/RuntimeError con probe conocido/SQL desconocido/runtime desconocido, sin submit y sin duplicar intentos ni consumo de capacidad.

Custodia: 26 fuentes protegidas exactas, incluidos resolver y los dos tests antiguos fuera del ownership; todas las definiciones scanning anteriores exactas por AST. Congelación de tests/runner/helper/config antes de cada RED, argv/UTC/exit/stdout/stderr/JUnit únicos. T08 terminó antes de RED y final; helper actual coincide con su receipt. No se restaura helper anterior ni se atribuye el histórico189 a los bytes nuevos.

## Límites e incidencias preservados

- Las lecturas iniciales sólo tienen las salidas de la herramienta, no recibos de subprocess separados.
- baseline-postcommit-controls: 4 fallos de fixture por hook SELECT antes de commit; no cuentan como RED. Corregido el hook con señal after_commit y seis controles baseline pasaron.
- green-minimal-regressions: 3 fallos del adapter de test por load ausente al alcanzar el tail; los RED originales fallaron antes por la carrera real. Se añadió load al adapter, sin quitar ni debilitar asserts.
- Pred189 queda con sus bytes/helper históricos. Final206 es una ejecución nueva con el helper terminal de T08 actual y las mismas fuentes congeladas.
- Heartbeat y tiempos son evidencia descriptiva CPU nativa, con adapter Catalog sintético; no son benchmark GPU ni garantía de latencia máxima.
- Bases SQLite privadas y staging durable de fallos se conservan como evidencia. No se realiza recuperación/retry/cancel.
- finalize-delivery y finalize-delivery-paths fallaron al consultar claves de manifiesto/cobertura con separadores Windows. Sólo el generador privado se normalizó; no se repitieron tests ni se modificó producción. La lectura ConvertFrom-Json de PowerShell tampoco toleró las claves de coverage; no cuenta como verificación.
- No aceptación global, calidad, tarea o hito; no writes en ledger/docs/Git.

Modelo/tokens/EUR/horasIA reales: NULL; sólo asignación estimada de root. No subagentes, goals, GPU, UI, WSL/Ollama, red, instalación ni Python del host. Docs/ledger/Git/decisiones/aceptación exclusivos de root.

DONE_WITH_CONCERNS: corrección concreta terminada; pendientes revisión fresca y QA independiente, sin aceptación de tarea/global/calidad.
