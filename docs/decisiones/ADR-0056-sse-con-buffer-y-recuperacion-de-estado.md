# ADR-0056 · SSE con buffer y recuperación de estado

- **Estado:** aceptada bajo delegación autónoma del propietario; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-08.
- **Relacionadas:** [ADR-0035](ADR-0035-despliegue-docker-y-ollama-wsl.md), [ADR-0047](ADR-0047-cola-empaquetada-en-app.md) y [ADR-0055](ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md).

## Contexto y alternativas

T-06 pide `GET /api/events`, replay desde un buffer, estado actual cuando el cursor queda fuera del buffer y keep-alive cada 15 segundos. No exige conservar toda la historia de progreso tras reiniciar. La cola tiene un `EventBus` limitado a 256 registros; SQLite conserva el estado de jobs e intentos, sin tabla de historial de eventos. La API pública actual valida Host/Origin, pero no posee una credencial pública: `engine_token` es privado de los engines y no se reutilizará en el navegador.

Se compararon ampliar el bus con buffer y recuperación de estado (O1), añadir un outbox SQLite transaccional (O2) y usar un servicio adicional (O3). Se elige O1 para el único runtime local. O2 queda como alternativa si se exige replay histórico durable o varios escritores independientes. O3 añade infraestructura y no resuelve por sí sola la ventana commit/notificación; no se añade Kafka ni Redis.

## Decisión

El stream tiene epoch de arranque/reset y secuencia global en memoria, distinta de `JobAttempt.last_seq`. El sobre JSON conserva `{id, type, ts, data}`: id entero positivo seguro en JavaScript y ts UTC con milisegundos. El identificador SSE es `epoch:seq`; el cliente conserva ese identificador completo. Se preservan la firma y la semántica interna de `EventBus.publish` y de su buffer para los consumidores existentes. El adaptador público traduce `job.error` a `job.failed` sin cambiar los terminales de engine ni fabricar intentos locales.

Replay y alta del suscriptor comparten una sección crítica para no perder eventos entre ambos. El buffer tiene 256 eventos; cada suscriptor admite 64 pendientes y hay un máximo de 32 suscriptores. Los frames tienen un límite de 64 KiB UTF-8 y los cursores 96 bytes. La publicación no espera al lector: overflow invalida y despierta/cierra ese suscriptor; la reconexión reproduce el buffer o recupera estado. No se descartan silenciosamente eventos ni se usa una cola de callbacks ilimitada entre hilos y event loop. Un cursor malformado se rechaza antes de empezar el stream; epoch antiguo, cursor adelantado o expirado requiere reset.

El heartbeat es un comentario SSE cada 15 segundos, sin ID ni cambio de progreso. Await, envío y cierre son acotados; el timeout de envío es 30 segundos. Disconnect y shutdown liberan suscriptores sin cancelar los jobs. Las operaciones SQLite y los locks nativos no bloquean el event loop.

La integración introduce una barrera breve compartida por los escritores del server y el bootstrap. Tras commit, una publicación fallida conserva los efectos durables y cambia el epoch mediante una vía independiente del publicador que falló. El bootstrap autorizado toma una lectura WAL, captura el estado y el cursor H y registra al lector para eventos posteriores bajo esa misma barrera. Es necesario integrar todos los escritores participantes; el bus aislado no acredita esa consistencia.

[ADR-0065](ADR-0065-comprobaciones-finales-de-metadata-bajo-barrera.md) permite
las comprobaciones finales de metadata existentes sobre entradas autorizadas
y staging propio bajo la barrera. Conserva la prohibición de bytes, hashing,
staging, cleanup, modelos, red y awaits dentro de ella; no elimina controles
del writer ni promete plazos absolutos de syscalls.

El reset viaja como `system.status`, con begin/chunk/end; sólo end confirma `epoch:H`. El cliente aplica la copia completa y después los eventos posteriores, o descarta una copia interrumpida sin avanzar su cursor. El snapshot incluye jobs activos autorizados y los terminales de hasta 64 IDs previamente conocidos por el cliente, para que una tarjeta no quede ejecutándose cuando el terminal ya salió del buffer. Un filtro de canción se autentica antes de replay/snapshot; el cliente no elige owner_id. Cambiar de filtro exige reset. Se limita el snapshot a 1.000 activos y chunks de 64 jobs y 64 KiB; un exceso produce un error explícito antes del stream, sin truncamiento oculto.

Antes de integrar el endpoint, se definirá y validará el OpenAPI compatible y la credencial pública dedicada. El cliente de navegador usará fetch/ReadableStream si precisa un header privado de sesión, sin tokens en URL ni reutilización del token de engines. La creación/transporte de esa credencial deberá conservar la UX local y la política de seguridad existente; esta decisión no añade una pantalla de autenticación ni afirma que el token esté implementado. Owner activo y pertenencia de canción/job se comprueban antes de emitir datos. El adaptador enumera campos públicos y evita exportar peticiones completas, terminales crudos, rutas, secretos o letras no solicitadas.

## Secuencia y límites

U1 implementa sólo el bus acotado y el adaptador/framing, con tests reales de replay/handoff, overflow, filtros, cierre, ID y privacidad. No añade endpoint, autenticación, barrera SQLite, snapshots ni cliente nuevo. La integración posterior conecta escritores, bootstrap autorizado, contrato API, route, cliente y E2E de reinicio. Se preservan los tests y terminales de T-04 y se revisan los cambios de seguridad de forma independiente.

No se añade una migración en O1. Si se elige posteriormente O2, requerirá un ADR y una migración posterior a la ampliación CPU pendiente; no se ocupa el 0006 reservado en ADR-0055. T-06/M1 permanecen abiertos hasta la verificación y sus criterios completos. La cadencia, memoria y ausencia de pérdida se prueban; no se afirman por el diseño.


## Rechazo anterior al commit

[ADR-0061](ADR-0061-rechazo-con-rollback-confirmado-sin-invalidar-el-feed.md) distingue rollback confirmado anterior a cualquier commit de incertidumbre durable: sólo el primero conserva ring/epoch/lectores y relanza la primera causa. Implementación y pruebas pendientes; no habilita el endpoint por sí solo.
