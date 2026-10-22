> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

SCOPED_CURRENT_NATIVE_QA_PASS

Baseline propia: {'passed': 428, 'skipped': 2}. Dos suplementos HTTP separados: {'passed': 2}.

Cobertura oficial actual de archivos completos, una sola traza y cero exclusiones:

- apps/server/app/queue/events.py: 52/54 = 96.296296%; excluidas 0.
- apps/server/app/queue/retry.py: 98/104 = 94.230769%; excluidas 0.
- apps/server/app/queue/recovery.py: 48/50 = 96.000000%; excluidas 0.
- apps/server/app/queue/cancellation.py: 32/34 = 94.117647%; excluidas 0.
- apps/server/app/queue/runtime.py: 336/369 = 91.056911%; excluidas 0.
- apps/server/app/queue/admission.py: 195/206 = 94.660194%; excluidas 0.
- apps/server/app/queue/dispatcher.py: 144/160 = 90.000000%; excluidas 0.
- apps/server/app/main.py: 99/103 = 96.116505%; excluidas 0.

Custodia: bootstrap PowerShell y runner archivados antes de lanzamiento; fuentes actuales archivadas antes de imports productivos. Copias de vecinos de QA1 final-prepared con todas las rutas históricas de escritura reescritas a QA2 antes de ejecución. copied-fixture-AST-parity.json demuestra AST completo normalizado por rutas, assertions/decorators/parameters exactos; original-six-canonical-AST-parity.json conserva la comparación con los seis originales. Canonical sources y tests no modificados. Los hashes antes/después y el inventario completo están adjuntos. No se ejecutaron runners históricos ni se reutilizaron sus trazas.

QA1 se inspeccionó readonly: primera baseline inválida escribió dos BD nuevas bajo fix2; root verificó 5355 originales intactos y birth de nuevos archivos UNKNOWN. Esos artefactos se mantienen. Wrapper final-prepared falló después de pytest PASS por JUnit inexistente; este actor usa final-current.junit.xml observado del argv. No se reconstruye FILETIME/Job con mtime. UUID/PID/UTC/argv y cleanup wait propios constan en birth/command. Bootstrap stdout/stderr reales; su PID/FILETIME/Job no observado se conserva UNKNOWN.

Evidencia nueva nativa Windows: SQLite de archivo migración0005/WAL, SELECT JOIN retryeligible y páginas400/400/1, dos streams misma Session y snapshot finito, backdated insert diferido, detach propio, recorrido1602 exacto sin omisión/duplicado, dos finally/pool0 y pico800 de esta distribución; no límite universal. native-current-evidence.json contiene muestras de SQL, recursos y cancelación emitidas en esta ejecución. native-owned-file-metadata.json lee metadatos de BD propias en modo ro.

Prioridad/FIFO global queued+retry en ambos órdenes, microUTC/tieID y801+801; altos inválidos/busy/unroutable/not_before/deps/cancel/deleted no bloquean CPU válida con GPU ocupada. Screening negativo compartido acotado por poll no sustituye validación fresca de writer/input SHA/capability/health; catálogo positivo fresco. Load ACK propio registra residencia incluso en resend ConfirmedAbsent; ACK perdido/status working/cancel ACK no inventan residencia. Se conservan capacidad, inputs e identidad inciertas, sin unload extranjero arbitrario.

NativeWinEvent dentro de UDF SQLite real y executor nativo: future inflight sobrevive cancel async hasta retorno real; reader finally/pool/executor join esperan E/S y ejecutan cleanup fuera del event loop. Repeated cancel/shutdown, misma instancia CancelledError y notas secundarias, startup/backup/dispose preservan causa primaria. No acredita preemption de kernel colgado ni deadline; clocks y scheduling cualificados para hilos actuales, sin SLA RT genérica.

Motor sintético y GPU1/CPU2 son política de algoritmo; CPU no descarga GPU. Dos HTTP MockTransport ACK-loss/EOF separados acreditan adapter sin socket HTTP real ni GPU. EventsBus U2 sólo progresoengine/eventos cubiertos, no SSEglobal. ID/payload/cursor frozen y efectos transaccionales, terminal durable único, retry sólo error durable máximo3 intentos/offload una vez; timeout/EOF/replay/invalidshape/postcommit inciertos permanecen unknown.

Skips actuales preservados literalmente en case-parity.json: privilegio symlink Windows. La frase heredada «probado en Docker Linux» del motivo no constituye prueba Linux de esta QA. Ruff check/format ocho productivos y diez tests canónicos y ledger-lint readonly tienen comandos y salidas adjuntos; no se arregló formato de copias privadas. No schema522 ni suites portables/globales ni wheel U1 repetidos: no cambios materiales de packaging.

Inspección4 A/B/D y adjudicación clean leídas; counter4/U1cinco y QA215/U1seishelpers se preservan. Historial initial/fix1/fix2/fix3 RED readonly, sin retroperfect TDD: fixtures tempranas incorrectas, GenuineRED/source-open desaparecida, encoding PowerShell y presupuesto actor4/root3 corregido siguen cualificados. No se presenta congelación global: arquitecturaT09 en rutas ajenas puede cambiar.

Alcance parcial: cadenas/manualretry/batchserie/postworker/assets/takesready/U3 futuros, ocho CA T04 abiertos hasta integración. UI/Playwright/PDF y global M1 n/a en esta fase, sin aceptación E2E o calidadproducto. Root conserva ledger/decisiones/Git/aceptación/meter. Peso2 estimado; modelo/tokens/EUR/horasIA reales NULL.

Incidente propio de entrega: el primer audit comparó líneas raw de CoverageData (incluyen líneas no sentencias) con JSON oficial de sentencias; AssertionError preservado. Diagnóstico propio y wrapper/gates corregidos sólo en QA2: el diagnóstico de intersección también falló por líneas de sentencias multilinea normalizadas; ahora compara sentencias menos missing de analysis2 oficial y conserva las líneas extra raw. Comandos fallidos de entrega histórica privada quedan cualificados fuera del gate de la baseline. Se corrigió además el gate que leía el exit previo del propio audit antes de su finalización. Todos los originales fallidos y diagnósticos se preservan. No se repitió pytest ni se modificó el producto.

