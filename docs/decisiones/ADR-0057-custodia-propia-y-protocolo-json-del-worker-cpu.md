# ADR-0057 · Custodia propia y protocolo JSON del worker CPU

- **Estado:** aceptada bajo delegación autónoma del propietario; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-08.
- **Relacionadas:** [ADR-0053](ADR-0053-postproceso-cpu-portable-en-el-server.md), [ADR-0055](ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md) y [ADR-0042](ADR-0042-proveedor-wddm-aislado-y-preparacion-observada.md).

## Contexto y elección

El cómputo CPU necesita un grupo propio que incluya FFmpeg y que no sobreviva sin control al server. Los helpers inspeccionados de engines y benchmark no ofrecen el contrato completo de nacimiento suspendido, aislamiento de handles, liveness y limpieza que requiere este worker; tampoco se trasladará la autoridad de auditoría del benchmark al producto. Se compararon reutilización directa, helper stdlib del server (O2) y extraer un paquete compartido. Se elige O2: módulos nuevos y pequeños del server, sin imports del benchmark ni dependencia de engine_common/torch. La extracción compartida queda para una necesidad real de reutilización, no para esta unidad.

## Nacimiento, terminación y custodia

En Windows, un Job Object propio no heredable con kill-on-close se crea antes del proceso. `CreateProcessW` crea suspendido y conserva los handles reales de proceso e hilo; se acredita la identidad y la pertenencia, se asigna al Job y sólo entonces se reanuda el hilo. No se presupone que un Popen suspendido conserve un hThread utilizable. Se limita la herencia a los handles de pipes autorizados mediante STARTUPINFOEX/handle-list, nunca el handle del Job ni todo el entorno del server. Se verifican límites, identidad y referencias antes de terminar o cerrar. Reutilización de un valor de handle no acredita el mismo objeto: se usará comparación de objetos mediante una referencia propia retenida cuando corresponda, y se conservará custodia desconocida ante contradicción.

En Linux, el supervisor propio queda fuera del grupo de trabajo, establece subreaper antes de crear el líder con sesión propia y conserva su identidad. Liveness del padre va por un pipe separado. EOF, cancelación o plazo inicia TERM/KILL del grupo propio, espera el líder y los descendientes adoptados y comunica cierre comprobado; el padre espera también al supervisor. Una señal de muerte del padre aplicada sólo al hijo inmediato no acredita la terminación de FFmpeg. No se mata por nombre, no se reutiliza un PID como autoridad y no se toca un proceso ajeno.

Los estados de custodia son `STARTING`, `OWNED`, `DRAINING`, `CLOSED_CONFIRMED` y `UNKNOWN_QUARANTINED`. Sólo el cierre completo comprobado permite liberar el slot y limpiar staging. EOF prematuro, miembros/handles desconocidos o lectores todavía activos no se convierten en `resources_returned=true` porque el líder terminó. El runtime y la reconciliación conservarán la ocupación mientras la custodia sea desconocida. Estas obligaciones aún no están probadas para el worker.

## Transporte privado

El IPC usa longitud uint32 en orden de red y JSON UTF-8 estricto, sin pickle ni objetos ejecutables. El sobre tiene exactamente `version`, `execution_id`, `epoch`, `seq`, `kind` y `payload`. Identidad y epoch deben coincidir; secuencia positiva y contigua por dirección. Se rechazan extras, duplicados JSON, números no finitos, tipos no estrictos, secretos, UTF-8 inválido, truncamiento y límites excedidos. El transporte no constituye autoridad SQLite ni prueba una publicación.

Límites iniciales: frame256KiB, total4MiB por dirección, profundidad20, colección256 entradas, string8192 caracteres, cola4 y stderr retenido16KiB. El límite total se comprueba además del límite de cada frame. El lector no conserva buffers ni callbacks ilimitados; EOF con datos incompletos es error explícito. stderr se drena o cancela según un plazo finito, sin confundir texto diagnóstico con resultado de negocio.

Se admiten `ready`, `request`, `progress`, **`take_result`**, `result`, `stop` y `closed`. `take_result` permite entregar hasta64 resultados independientes antes del resumen final y publicar cada toma mientras otras siguen activas, como requiere ADR-0055. Por ello se ajusta la propuesta privada: máximo132 frames y hasta64 progress/take_result por dirección, manteniendo el total4MiB. Un resumen `result` global no se repite; `closed` lo sigue o responde a una cancelación/liveness explícitamente acreditada por la sesión. Los resultados por toma no se confunden con terminales globales. La validación de sus DTO y la autoridad de publicación permanecen en el padre.

## Fuentes primarias comprobadas y límites

Antes de código nativo se consultaron [CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw), [PROCESS_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-process_information), [STARTUPINFOEXW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-startupinfoexw), [UpdateProcThreadAttribute](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute), [AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject), [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) y [CompareObjectHandles](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-compareobjecthandles). Las firmas, la lista de handles heredables, el nacimiento suspendido y la comparación de objetos están documentados. Esa lectura no acredita un binding ctypes ni su layout en ejecución; se probarán con procesos reales y testigos ajenos.

Para Linux se consultó la documentación primaria de [man-pages de kernel.org](https://www.kernel.org/pub/linux/docs/man-pages/book/man-pages-6.13.pdf) sobre subreaper y señales de muerte del padre. No acredita comportamiento nativo, supervisión completa ni limpieza de este worker. La verificación real Linux irá en Docker CPU propio, sin GPU ni servicios ajenos.

## Unidades y verificación

Primero protocolo puro y límites, con regresiones causales y cobertura del módulo completo. Después custodia Windows/Linux y pipes, con nacimiento/grandchild, testigo ajeno, timeout/cancelación/pipe bloqueada, muerte real del padre y handles reutilizados. La integración de audio/FFmpeg, reservas CPU2, publicación y BD se hará después. Cada unidad mantiene TDD, revisión fresca y QA. No se modifican los contratos privados ya aceptados ni los JSON públicos en esta primera unidad. T-05/M1 siguen abiertos; ni un decoder ni un diseño prueban custodia o slots.
