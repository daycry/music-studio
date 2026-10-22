> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# B4-01 / R09-T09 — entrega FIRSTcause

Corregidas exclusivamente tres fronteras: proof del episodio→cierre del sensor; startup de OwnedProcess→cierre; cuerpo del contexto→cierre del coordinador. Excepción primaria preservada con identidad y tipo; custodia secundaria tipada, acotada y protegida. Startup conserva referencia fuerte al OwnedProcess incompleto en la excepción original. Sin fallo primario, el cierre sigue propagando su error real. No se libera anticipadamente ninguna reserva ni se repiten efectos.

RED causal: dos variantes por frontera, identidad primaria esperada; código original emitió WorkerFailure secundario de terminación del Job propio. Excepciones CONTROLADAS, recursos Windows reales; ningún mock del kernel ni fallo de colección. Evidencias físicas antes de cada ejecución, argv/UTC/PID/JUnit/stdout/stderr y nacimiento tipado conservados en red-process, red-episode y red-coordinator.

GREEN dirigido: diez casos; seis de identidad/registro fallido, uno de registro de referencia nativa fallido y tres de propagación sin causa previa. Estos tres últimos son comprobaciones de preservación que ya pasaban, no nuevos RED causales. Baseline final03: **263 PASS, 0 FAIL/ERROR/SKIP, mismos 13 deseleccionados**; 253 originales semántica/AST/asserts/decoradores/params intactos + 10 casos. UUID 9ad4ae34-66d7-436e-8ac4-d2f00039d0f9; 267 trazas frescas, originales copiados ANTES de combine keep. Seis módulos WHOLE ≥80 %, cero exclusiones. final01 también pasó, pero es histórico: lint posterior exigió cambios reales de bytes; final02 también es histórico por el RED adicional del registro de referencia; sólo final03 acredita las fuentes finales. No unión ni promedio.

- scripts\eval\benchmark_canonical_integration.py: 86.194030 % WHOLE; 0 excluidas.
- scripts\eval\benchmark_canonical_runtime.py: 84.584178 % WHOLE; 0 excluidas.
- scripts\eval\benchmark_coordinator.py: 83.741648 % WHOLE; 0 excluidas.
- scripts\eval\benchmark_episode.py: 86.311787 % WHOLE; 0 excluidas.
- scripts\eval\benchmark_process.py: 82.666667 % WHOLE; 0 excluidas.
- scripts\eval\benchmark_runtime.py: 80.516899 % WHOLE; 0 excluidas.

Ownership/current_sources: sólo seis archivos autorizados, tres producción y tres tests. Contexto protegido separado y byteexacto. Templates aceptados de baseline1 sólo leídos y copiados antes de adaptación; ningún ledger, documento, Git ni archivo reservado del padre escrito. Formal4→5 conservado; revisión componente fresca y QA root pendientes.

Incidente privado conservado: lint02 actual ExitCode null after Start-Process/WaitForExit; shell stopped early and format did not run. Original script/logs retained, explicit Diagnostics.Process launcher repaired; lint03 and lint04 capture true exits. Not product RED.

TDD n/a: prosa y configuración/orquestación privadas.

Límites: Initial RED templates persisted typed PID/creation_time/Job membership and cleanup, but numeric handle/object refs and individual Popen UTC were added only before green-nine/final01; no retrospective birth claim. Preliminary shell read/setup command UTC/PID were not individually archived; UNKNOWN. Child stderr DEVNULL; complete RPC capture UNKNOWN. Native cleanup disposition is conservative; Job emptiness alone never proves return. Physical ReadFile blockage/reader-close universal proof UNKNOWN. Not independent QA or full T09/M0 acceptance.

Pendientes separados: B4-02 deadlines, B4-03 shared startup budget, B4-04 context binding, R09-T13 CLI migration, fresh component review and root QA, GPU160, calibration, 13h cadence, FINAL/CLI/M0 acceptance. No aceptación completa.

Historial privado adicional: se editÃ³ por error un helper de entrega no ejecutado durante final02; versiÃ³n conservada y bytes restaurados desde archive antes del final. NingÃºn fuente de producciÃ³n/test/runner/instrument ejecutado cambiÃ³. UTC/PID/hashes en unused-helper-edit-history.json. MÃ©tricas reales modelo/tokens/EUR/horas IA NULL; CLI original reservada al padre e intacta.

RED adicional red-reference: la implementación parcial emitía OSError controlado al adjuntar la referencia, en vez del PrimaryFailure original; Job/lector propios reales ya ejercitados. El guard mínimo conserva identidad, traceback/self y registro tipado del cierre. Digest secundario acotado al primer argumento string (máximo 4096 caracteres), tipo máximo 128; no se invoca __str__ arbitrario ni se promete hash del mensaje completo.
Verificación terminal sólo lectura: 21273/21273 ficheros NONCLI inventariados en ese instante, cero diferencias de nombres/hashes propios/protegidos y cero cambios de funciones originales; selección original como subsecuencia exacta. 267 RAW, 268 nacimientos observados: 235 CLOSED_CONFIRMED, 33 UNKNOWN_QUARANTINED; dos trazas startup siguen UNKNOWN.
