> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# U1 retomada: entrega concreta con baseline fallida

No se acepta U1 como completa. No se repite el fallo funcional observado en final03. Sólo los seis archivos OWNED tienen cambios; los originales de proceso/episodio/coordinador y los tres módulos protegidos siguen byteexact.

## Cambios

StartupBudget conserva un deadline absoluto y valida valores estrictos. OwnedProcess registra referencias antes de birth, conserva actores/Popen/Job/transportes en quarantine, revoca irreversiblemente, impide gate de birth tardío y mueve consultas/write/close a actores retenidos con espera finita. El protocolo hijo comprueba D antes del handler; el mux conserva su activate original con un latch de LIVE que no revive tras revocación. Sólo exit/EOF/pertenencia/joins observados permiten publicación de CLOSED. Las clases de episodio y coordinador admiten startup_deadline_ns y conservan inicio+2s para cada episodio. La espera de arranque evita la reacquisición no acotada de Condition.wait.

## TDD y ejecución real

RED: test_delayed_actual_popen_revokes_before_late_gate falló con caller blocked past original startup budget in native birth — red-native/command.json, stdout/JUnit y witnesses previos a la aserción. Producción nativa antigua byteexact en su archivo before.

RED: test_episode_entry_budget_includes_real_context_read falló con failure=None y nacimiento completado después de demora de contexto — red-propagation-fixture-repair. El primer intento red-propagation PASS no es RED; fixture inicial incorrecta/margen demasiado corto, conservado. La corrección de fixture ocurrió antes del cambio al episodio.

GREEN inicial: 3 casos native; GREEN cohesionado: 6 casos native. Sin PID ficticio ni fake kernel type. La demora ocurre en un wrapper pasante tras Popen real o alrededor de asignación real; no acredita un kernel físicamente bloqueado. Events, polling, threads, profile, hashes, copias, cobertura y writes de witnesses son observadores declarados.

Actual final03: {'cases': 300, 'pass': 269, 'failures': 1, 'errors': 30, 'skips': 0}; original274 orden exacto=True; 13 CPU deselections exactas=True. Los 26 casos nuevos (20 pure + 6 native) están incluidos y allpass=True.

Fallo real: test_factory_owns_actual_workers_and_fresh_consumer_binding durante consume_runtime, WorkerFailure(worker_pipe_eof). Véase actual-functional-failure.json y final03/stdout.txt. Actor externo OwnedProcess.call -> _NativeAction.wait -> mux.call; EOF del reader original. No se conoce por qué terminó el hijo: stderr original era DEVNULL, no se reconstruye una causa ni se cambia código protegido. Alcance de corrección posible OWNED: benchmark_process.py (actor/call/custodia), benchmark_coordinator.py (sampler/reserva) y sus nuevos tests; canonical runtime/integration permanecen READONLY.

30 errores adicionales son fixture harness_module ausente. -p conftest colisionó con el conftest del root; no son 30 fallos de producto, pero invalidan la regresión completa. No se ejecuta un cuarto baseline ni reparación seguida de retry después del fallo funcional.

## Historial de harness

final01: colección SyntaxError por sustitución textual dentro de literales; ningún caso/native birth. Reparado por transformación AST de PHASE top-level exclusivamente. final02: 119FAIL/130PASS/51ERROR, copies de runtime importadas y coverage ausente en el intérprete base de los hijos; 0 child traces. Materialización privada corregida, sin cambios productivos/aserciones. final03 verifica rutas reales de los siete runtime antes de cada test y hereda site-packages para el hijo. Los dos intentos inválidos, RAW y command receipts se conservan separados; no se unen sus trazas al actual final03.

## Cobertura WHOLE actual

| Módulo | Oficial líneas+ramas | Excluidas |
|---|---:|---:|
| scripts/eval/benchmark_startup.py | 100.000000% | 0 |
| scripts/eval/benchmark_process.py | 84.277457% | 0 |
| scripts/eval/benchmark_episode.py | 86.948529% | 0 |
| scripts/eval/benchmark_coordinator.py | 71.926230% | 0 |

Gate cuatro WHOLE=False; datos exclusivamente de la baseline FALLIDA, mismo UUID 8162851a-bc5a-4fe9-a1b8-938fb6d8e704. RAW preservado antes de combine, sin union histórica/extracción/exclusiones/promedios. Las trazas nativas ausentes quedan UNKNOWN en native-counts.json.

## Límites y entrega

U2 SourceGuard no implementado. U3 binding/canonical factory no implementado. U4 caller compartido completo no implementado: canonical create_session/read/consume, RuntimeChannel y run_owned siguen con sus entradas actuales protegidas. El deadline se fija antes de encode/checks en las entradas OWNED, pero los source/hash/context reads síncronos no ofrecen retorno finito bajo bloqueo físico hasta conectar U2. Las syscalls ya despachadas pueden acabar tarde; el protocolo rechaza D expirado antes de handler y quarantine retiene originales. No se garantiza exit de proceso/thread bajo bloqueo arbitrario del kernel/GIL/scheduling. Sin censo universal de recursos o reconstrucción postmuerte.

No GPU/WSL/Ollama/Docker/UI/PDH/download/install/host Python/external network, ni docs/ledger/Git/acceptance/meter mutados. El recipe original contiene sus fixtures CPU de loopback, no nuevos servicios. Historial FIRSTcause/formal3/4/T10 conservado; próxima revisión integrada5 corresponde a Root después de U2–U4. Modelo/tokens/EUR/AIhours NULL, sin facturación inferida. fresh review y QA Root pendientes.

Estado: U1 concreta revisable, NO completada/aceptada; fallo funcional entregado una vez con la prueba original.

Ruff final readonly: check exit0; format --check exit1 en benchmark_process.py (cinco restantes formateados). Recibo final-static/command.json. No se modifica la fuente tras el fallo nativo ni se vuelve a ejecutar la baseline. Este gate está también pendiente.

