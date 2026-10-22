# ADR-0043 — Identidad durable de cada intento de ejecución

- **Estado:** aceptada; implementación, revisión y QA pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación autónoma del propietario
- **Ámbito:** M1/T-04 y T-05; concreta los reintentos y la recuperación de ADR-0018

El engine conserva en memoria el resultado de cada `job_id`, incluso cuando falla. Reenviar ese ID recupera el resultado anterior; descargar el modelo no elimina ese registro. Un reintento después de un error confirmado necesita una identidad nueva, mientras que recuperar un acuse perdido requiere conservar la identidad enviada. El job lógico del server y el intento del engine cumplen funciones distintas.

Se compararon un historial dentro de `job.request`, una relación tipada y un cambio del protocolo `/v1`. Se elige **una tabla tipada `job_attempt`**, mediante una migración aditiva posterior al esquema inicial de 23 tablas. `job.request` conserva la petición de dominio, incluidas las referencias aún no resueltas. Cada intento guarda la petición contractual resuelta e inmutable; no se mezcla con un historial opaco ni se cambia la API de los engines.

`job_attempt` tendrá los campos comunes `id`, `owner_id`, `created_at`, `updated_at`, `deleted_at`, además de `job_id`, `ordinal`, `engine_id`, `model_id`, `mode`, `engine_request`, `last_seq`, `status` y `terminal`. La pertenencia al usuario debe coincidir con la del job. El par `(job_id, ordinal)` es único. `engine_request` se valida como `JobRequest`, con semilla, parámetros, inputs resueltos y hashes; las opciones necesarias para cargar el modelo quedan también congeladas y validadas, sin secretos. El ID ULID del intento es el `job_id` de `/v1` y determina `tmp/<attempt_id>/`.

Los estados del intento son `prepared`, `submitted`, `succeeded`, `failed` y `cancelled`. `prepared` significa **posiblemente enviado**: no demuestra que el POST no haya ocurrido. `last_seq` y el efecto de cada evento se guardan en la misma transacción, incluido su terminal validado. Un evento repetido no vuelve a publicar ni a postprocesar salidas.

`job.attempt` cuenta reservas de intentos: empieza en cero y el máximo por defecto es **tres intentos totales**, equivalentes a dos reintentos. Antes del primer POST se reserva y congela el intento en SQLite. Sólo un terminal de error durable con `retryable=true`, presupuesto disponible y ausencia de cancelación permite reservar el siguiente. Esa reserva y el estado anterior se actualizan en una transacción. Un acuse desconocido, BUSY de preadmisión, desconexión o reinicio no consume otro intento. Excepción ([ADR-0090](ADR-0090-reintento-acotado-de-intentos-dudosos.md)): si tras un reinicio el engine confirma la ausencia y el reenvío con el mismo ID no es seguro, el server registra un error retryable y se reserva un intento nuevo. La transición a offload por `VRAM_EXCEEDED` puede ocurrir una sola vez y sólo si el descriptor lo permite; cuenta dentro de ese presupuesto.

La recuperación consulta el estado del intento vigente y reengancha su cursor. Si hay que reenviar, utiliza exactamente el mismo ID y payload congelado. Un registro ausente sólo se considera probado mediante una respuesta de estado válida; no mediante un error de transporte. Tras un reinicio del engine confirmado, se reinicia el cursor del mismo intento cuando corresponda. Un terminal exitoso durable continúa en CPU sin volver a generar.

Un directorio existente sin terminal durable no prueba éxito. Se conserva y reconcilia únicamente la salida cuya propiedad esté acreditada; no se sobrescribe ni limpia a ciegas. Las entradas duraderas se conservan fuera de ese directorio o se restauran por sus hashes congelados. La propiedad y el confinamiento se verifican antes de cualquier traslado o limpieza. El código actual del engine no garantiza rechazar toda salida preexistente; el server no puede basar su seguridad en esa afirmación.

La cancelación lógica durable impide nuevos intentos y se propaga al vigente. Si el terminal exitoso ya se aceptó transaccionalmente antes de la cancelación, se conserva; si la cancelación se confirmó primero, no se publica después un take listo a partir de eventos tardíos. El reintento manual crea otro job lógico y sólo reutiliza takes fallidos del mismo usuario y canción. Conserva el historial de los intentos anteriores.

Snapshots y backups deben conservar esta relación, las peticiones congeladas, cursores y terminales. Restaurar un job en curso sin identidad de intento suficiente exige reconciliación; no autoriza inventar el ID enviado. El esquema inicial de 23 tablas permanece como baseline histórico y la tabla nueva se incorpora mediante otra migración. Las salidas y el manifiesto del intento ganador mantienen su relación con el job lógico y las variantes existentes.

La implementación debe probar errores retenidos, pérdida de acuse, reinicios entre reserva y POST, replay de eventos, límites de reintento, offload único, cancelación y restauración, además de propiedad de temporales y variantes. Esta decisión permite trabajo técnico CPU/mock bajo ADR-0037; no acredita el benchmark M0, calidad musical ni aceptación de un modelo.


Esta decisión precisa la referencia de CONSTITUTION §2 al esquema completo inicial: su baseline es el aprobado originalmente; una relación decidida después se incorpora de forma aditiva, sin reescribir aquella migración ni su evidencia. Datos y constitución se actualizan juntos.
