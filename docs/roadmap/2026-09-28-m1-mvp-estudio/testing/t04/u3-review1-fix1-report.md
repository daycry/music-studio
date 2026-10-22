> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# U3 review1 fix1 — entrega para revisión fresca

Corregidos los dos Important deduplicados de root; sin cierre de tarea ni aceptación global.

Reintento: generación con done durable conserva succeeded e historial completo; se crea job lógico nuevo con la request/seed/N originales y sólo los índices failed autenticados por fallo propio de post.audio, arista usuario/canción, entradas e identidad del intento vigente. La comprobación se repite bajo writer. Un lógico marcado failed después de done tampoco permite omitir esa autenticación. Prepared/submitted/ausente/ordinal desconocido no autoriza retry. El helper failed anterior se conserva; el test histórico añade un fallo CPU propio explícito manteniendo todas sus assertions.

SQL: precarga acotada por identidad en references/admission, chunks de 400, activos/padre/aristas/intento ganador/assets/takes; assets ambiguos limitados a dos por identidad mediante ventana SQL. Caché sólo de esta sesión/transacción/ventana, nueva en cada poll y reserva. Sin cache global ni nuevos módulos. Ownership, último terminal, input hash, staging/reserva y SHA fuera de writer conservados. Dispatcher/chains protegidos exactos.

Baseline final: 506 PASS, 2 SKIP, exit 0; original471 assertions conservadas. Primera corrida y su cobertura se retienen como históricas tras el refuerzo causal adicional; no unión de traces.

Cobertura oficial completa de un único trace actual, cero exclusiones:

- `apps/server/app/queue/manual_retry.py`: 92.93 %.
- `apps/server/app/queue/references.py`: 98.36 %.
- `apps/server/app/queue/admission.py`: 94.25 %.
- `apps/server/app/queue/dispatcher.py`: 89.63 %.
- `apps/server/app/queue/chains.py`: 98.80 %.

Conteos de SELECT realmente ejecutados (fuentes SHA antes/después y statements originales retenidos; hipótesis estáticas no son benchmarks):

- 400-ready-beats: 2404 → 11 SELECT.
- 64-shared-post-inputs: 132 → 6 SELECT.

RED genuinos antes de producción: original succeeded + own post failure rechaza Owned failed generation required; 400 candidatos exceden16 con2404 SELECT; 64 inputs exceden8 con132 SELECT; lógico failed tras done sin post propio DID NOT RAISE. Ver stdout/stderr/argv/UTC/exit/JUnit y archivos archive-* anteriores a cada ejecución. Los fallos privados de fixtures se conservan separados y no cuentan como RED.

RED: apps/server/tests/test_queue_manual_retry.py::test_queue_manual_retry_succeeded_generation_own_post_failure_native falló con Owned failed generation required · 2026-10-08T05:07:45.141707+00:00

RED: apps/server/tests/test_queue_references.py::test_queue_references_400_ready_beats_native_query_bound falló con AssertionError: 2404 SELECT >16 · 2026-10-08T05:08:48.042833+00:00

RED: apps/server/tests/test_queue_references.py::test_queue_references_shared_64_post_inputs_native_query_bound falló con AssertionError: 132 SELECT >8 · 2026-10-08T05:08:57.725625+00:00

RED: apps/server/tests/test_queue_manual_retry.py::test_queue_manual_retry_failed_logical_done_cannot_skip_post_authentication falló con DID NOT RAISE ValueError · 2026-10-08T05:18:39.455632+00:00

Paginación nativa 801: 400/400/1, finita ante inserción tardía y objetos detached. Negativas y revalidación concurrente de fallo post bajo writer cubiertas. T05 sólo inyección durable SQL, no FFmpeg/manifiestos/worker real. El conteo400 usa400 análisis de3 takes ready; el de64 usa una cadena real de64 bindings con artifacts sintéticos compartidos. No afirma latencia ni rendimiento GPU.

Ruff check y format --check exit0. 67 archivos protegidos exactos; assertions/decorators/parametrización previos preservados por AST. Current source copies y mapas antes/después incluidos. Helper global actual congelado, cli-metadata de t08-fixture-owner-fix3 terminal observado antes de verificación final; no se restaura ni atribuye una traza vieja a nuevos bytes.

Cleanup observado: fixture finalizers terminados y poolcheckedout0 cuando disponible; wait del child gestionado concluido. Metadatos stat Windows reales archivados. FILETIME/Job/cursorhandles UNKNOWN. DBs privadas conservadas como evidencia, no se declara borrado. Inventario NONCLI completo excluye sólo los cuatro ficheros top reservados del padre y el propio inventario.

Guías tdd y debug-root-cause1.22.0 aplicadas. Hipótesis confirmadas por REDs nativos: guarda de estado demasiado estricta y luego bypass por estado lógico; SELECT por referencia bajo writer. Se descartan fallos de imports/API/colección como evidencia causal. Gotcha propuesto a root: autenticar fallo downstream por causalidad durable, no estado del caller; mantener cachés DB locales a transacción. Docs/memoria exclusivos root.

Model/tokens/EUR/AIhours reales NULL; sin estimaciones monetarias inventadas. No Git/ledger/docs/decisiones, red/install/host Python/GPU/UI/WSL/Ollama ni producción T05. Pendientes revisión fresca, QA independiente, I01 y T04 completo.
