> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Diagnóstico privado de autoridad de drain — H1 continuación

OWNED[]. Un único caso Linux, sin cambios en producto ni tests del repositorio. La medición 801 tenía adjudicación terminal antes de este despacho. No H2, repeticiones, suite68, cambios de timers ni nuevas aceptaciones.

**Resultado observado: cierre inseguro reproducido bajo entrega controlada de bytes reales.** El primer `LinuxGroup.terminate(5)` devolvió realmente True, `unknown=False`, supervisor esperado con salida 0 y los tres pidfds válidos/señalados. `close(5)` devolvió True; el owner terminó CLOSED_CONFIRMED/cancelled, release_gate=True. El testigo ajeno estaba vivo antes de la decisión. Las wrappers no sustituyeron esos retornos ni las respuestas del kernel.

| Evento | monotonic_ns real | Retorno/bytes |
|---|---:|---|
| native_read_held | 22871786893638 | 000000107b |
| cancel_requested | 22871786950047 |  |
| terminate_enter | 22871787882280 |  |
| terminate_return | 22871994633469 | True |
| drain_delivery | 22871994684859 | 000000107b |
| native_stdout_eof | 22871995837721 |  |
| terminate_enter | 22871998247537 |  |
| terminate_return | 22871999294393 | True |
| close_return | 22872000060764 | True |
| joined | 22872000213089 | CLOSED_CONFIRMED |
| decision_before_assert_rescue | 22872000799961 |  |

El prefijo real 00000010 anuncia un cuerpo de 16 bytes, pero sólo llegó 7b (un byte). La lectura física guardó 000000107b durante OWNED y lo entregó durante DRAINING con stop=True. `Owner._run` llama `_read(parsing=False)` (custody.py:250); `_read` añade los bytes a stdout pero omite `decoder.feed` (custody.py:188). A EOF, `decoder.finish()` sólo rechaza su propio buffer pendiente (pipe_protocol.py:345). Al no recibir estos bytes, el decoder conserva vacío el buffer del último mensaje válido. El gate de custody.py:268 combina autoridad kernel real, EOF, ausencia de bad y group.closed: así acepta el cierre pese al frame truncado. Fuente esperada: si ese frame entrara al decoder, finish rechazaría EOF incompleto; bad quedaría sticky, release_gate=False y UNKNOWN_QUARANTINED/transport_error. Esto explica causalmente la aceptación insegura del caso H1, no demuestra el calendario físico de la QA histórica.

No hubo bloqueo de cierre en esta corrida: `_await(final)` devolvió True, control recibió el final real y EOF, process.wait devolvió 0, native_process_refs_waited=True. Las BlockingIOError del control fueron reales y tratadas por `_events`, no errores fatales. El líder PGID8 estaba vivo/no reapado a la entrada del primer terminate; tras el wait real ya no existía, conservándose los pidfds señalados. El journal original y los nacimientos/argv/kernel/UTC están en proof-native1; no se interpola metadata histórica. **Por qué el intento anterior devolvió False permanece UNKNOWN**: esta corrida no reprodujo ese retorno.

**Límite relevante de observador:** el JUnit es 1 FAIL, exit1, por EBADF posterior a la decisión. finish_observer cerró el pidfd del testigo; la wrapper de contain_unknown intentó volver a observarlo antes de reenviar la llamada de rescate. Esa llamada no fue reenviada. El owner ya había cerrado su grupo y publicado el recibo y la prueba previa al rescate. El error privado no es un RED causal de producto. No se corrigió ni repitió la sonda; código, JUnit y error quedan originales. No hay GREEN ni aceptación.

Dos errores de bootstrap previos al único caso se conservan en history/bootstrap0 y bootstrap1: WinError206 por argumento largo y FileExistsError por directorio de preparación existente. Ninguno creó un contenedor ni cuenta como RED. Se usó un archivo privado de entorno y un nuevo directorio de copias antes de la única ejecución real.

Contenedor propio con imagen sha256:fa0b727b54163f6cd26ab0e9fc4cec2da868ae9bdcac87b5e4cd242ecb019e9e, UID/GID65532, cap-drop ALL, no-new-privileges, read-only, network none, pids128, memoria1GiB, CPU2, tmpfs128MiB; código/herramientas privados y sin GPU/pull/build/install. CID64 capturado antes de start; start/inspect/remove/gone con PID/UTC/argv/salidas originales en actor-command-accounting.json. Remove exit0 y gone exit1/no such object. Grupo propio cerrado antes del rescate; testigo sobrevivió hasta la decisión. Exit/wait exacto del testigo tras la decisión UNKNOWN por falta de flush; salida del runner padre UNKNOWN porque Start-Process registró ExitCode null. No se sustituye por el exit del wrapper.

Custodia: fuentes protegidas antes/después exactas, copias físicas host gestionado y herramientas antes de importar/ejecutar; guards de la copia privada antes de los spawns y después. Las versiones de bootstrap y la adaptación privada están preservadas. TCB explícita: kernel/OS/libc e intérprete/stdlib/base runtime de imagen fijada sin exportación física independiente; host intérprete/stdlib/Windows. No existe auditoría exhaustiva de módulos transitorios cargados: no se afirma cierre total. No se retrorepara esa limitación. Cobertura n/a por cero cambios de producción; raw tracer conservado, sin gate aceptado.

Siguiente decisión corresponde exclusivamente a root: convertir la reproducción H1 en RED conductual genuino y aislar la validación del framing durante drain antes de un fix mínimo. No basta cambiar reason ni inferir éxito del journal. QA67/1 histórica, formato/contracts1 y revisión/QA frescas siguen abiertos. Esta unidad sólo entrega observación causal acotada; no modifica ledger, docs, Git, decisiones, conocimiento ni medidores. Tokens/modelo/EUR/horas NULL: sin proveedor de uso verificado.
