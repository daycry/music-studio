# T-06 · Preparación de la integración transaccional y HTTP

Fecha: 2026-10-09. Este documento prepara la siguiente unidad del dev-cycle;
no acredita que el endpoint esté implementado ni cambia el estado de T-06.
El estado permanece exclusivamente en [tasks.md](../../tasks.md).

El [diseño integral](integration-design.md) recoge las alternativas y la
elección O1 del orquestador. Se ha despachado el cliente fetch con ownership
separado de la cola. La integración de escritores espera fuentes actuales
verificadas; [ADR-0065](../../../../decisiones/ADR-0065-comprobaciones-finales-de-metadata-bajo-barrera.md)
precisa los controles finales de metadata conservando los vigentes.
La elección no equivale a una entrega.

El [contrato del cliente](client-contract.md) precisa el consumidor obligatorio
de snapshots, la reentrada de callbacks, el ciclo de credenciales y el cierre
acotado. El cliente ya tiene revisión3 A/B/C/D limpia y
[QA independiente de222 casos aceptada](client-independent-qa1.md).

El [contrato HTTP](stream-http-contract.md) fija query, errores y límites para
la unidad de integración. Su código y exportación canónica todavía no existen;
la propuesta OpenAPI sigue siendo una preparación, no una ruta implementada.

## Comportamiento que debe quedar disponible

El navegador obtiene una sesión local, abre `GET /api/events` y recibe el estado
de sus jobs. Después de una desconexión, recupera los eventos pendientes o una
copia coherente del estado actual, sin perder el terminal de una generación.
Se aplican [ADR-0056](../../../../decisiones/ADR-0056-sse-con-buffer-y-recuperacion-de-estado.md),
[ADR-0058](../../../../decisiones/ADR-0058-sesion-publica-local-para-eventos.md) y
[ADR-0061](../../../../decisiones/ADR-0061-rechazo-con-rollback-confirmado-sin-invalidar-el-feed.md).

## Piezas existentes y conexión pendiente

| Pieza actual | Conexión pendiente |
|---|---|
| `LocalSessionRegistry.validate/revalidate` | Validar el header al abrir y revalidar la sesión durante replay, espera y envío. |
| `TrustedFeedScope` y certificados internos | Comprobar pertenencia vigente en SQLite; un certificado no acredita pertenencia posterior a un borrado. |
| `EventBus.subscribe` | Mantener su alta en el event loop y coordinarla con la lectura WAL y H; no llamarla desde un hilo sin loop. |
| `PublicationCoordinator` | Compartir una instancia entre todos los escritores participantes y el bootstrap. |
| `EventConsumer` coordinado | El runtime todavía lo construye sin coordinador. |
| `build_snapshot` y DTOs cerrados | Consultar SQLite con autorización y límites antes de construir el reset. |
| Rutas de sesión y middleware local | Añadir el stream con contrato OpenAPI verificado antes del routing. |

`TrustedFeedScope` ya evita mantener un conjunto creciente de jobs. No hace falta
sustituirlo por una lista de 64 jobs ni aceptar owner aportado por el cliente.

El cliente actual en `apps/web/lib/events.ts` ya usa `fetch` con
`credentials:omit` y el header `X-Studio-Session-Token` requerido por ADR-0058.
El componente incorpora lectura incremental UTF-8, parser SSE, reconexión,
`Last-Event-ID` y cancelación. Los controles begin/chunk/end se aplican de
forma atómica y el cursor se confirma después del consumidor obligatorio.
Las222 pruebas CPU usan transporte simulado: todavía no acreditan una
conexión autenticada contra el servidor ni un recorrido de navegador.
El componente tiene aceptación técnica tras revisión3 y QA independiente;
la integración HTTP/allwriters permanece pendiente.

La [propuesta OpenAPI del stream](events-openapi.proposed.json) conserva todas
las operaciones vigentes y añade `/api/events`; pasa el linter estructural y
el diff sin cambios rompedores. Sus controles de snapshot se generan desde los
DTOs actuales, incluidos los límites y los objetos cerrados. Es una propuesta,
no el contrato canónico generado por FastAPI ni un endpoint registrado.
Antes del handler se fijarán los nombres de query (`song_id` y `known_job_id`
repetido en esta propuesta), el rechazo explícito por exceso de snapshot y
el tratamiento del cambio de filtro. La validación estructural no prueba
autorización, igualdad entre cursor e ID, WAL ni transporte.

## Escritores que debe cubrir la integración

La inspección del código identifica estos participantes; la unidad deberá volver
a comprobar el inventario después de la entrega de procedencia sintética:

- `admission`: dependencias, reserva, captura de procedencia y acknowledgement.
- `chains`: creación de generación, takes y dependientes.
- `cancellation`: intención de cancelación y terminal local sin intento.
- `recovery`: interrupción al arrancar e incertidumbre de un intento.
- `retry` y `manual_retry`: nuevo intento o cadena hija.
- `events`: progreso, stage, telemetría y terminal confirmado del engine.

Los cambios que afectan al estado público deben emitir un batch certificado
después del commit o invalidar el feed de forma explícita. Los writes privados
también deben respetar el orden de locks cuando participen en la misma barrera.
No se permite red, lectura de bytes, hashing, staging/cleanup de ficheros,
carga de modelos ni awaits bajo ella. Sólo las comprobaciones finales de
metadata descritas en ADR-0065 pueden permanecer dentro del writer coordinado.
Las futuras mutaciones de dominio y publicación CPU deberán usar esta misma
integración; no se puede afirmar cobertura de escritores que aún no existen.

## Orden de ejecución y pruebas de aceptación

1. Tras liberar el ownership de la unidad sintética, ampliar el alcance declarado
   de T-06 con los escritores afectados y generar un nuevo brief determinista.
2. Escribir primero un RED real de SQLite WAL: un escritor y un bootstrap
   concurrentes no pueden dejar un cambio fuera tanto del snapshot como del feed.
   Conectar después la instancia compartida y conservar los casos existentes.
3. Probar los escritores de arriba, rollback confirmado, commit incierto,
   publicación fallida e interrupciones. El éxito durable nunca se reenvía por
   un fallo de notificación. El rechazo confirmado no cambia epoch ni lectores.
4. Validar el OpenAPI y su compatibilidad. Probar la ruta con sesión auténtica,
   filtro de canción, IDs conocidos, borrado, revocación, cursor inválido,
   reconexión, límites, heartbeat, disconnect y lector lento.
5. Conectar el cliente: aplicar begin/chunk/end de forma atómica, conservar el
   cursor sólo al terminar el snapshot y descartar una copia interrumpida.
6. Revisión independiente, QA y recorridos Docker/navegador E2E-01 y E2E-06.
   Sólo entonces evaluar los criterios completos de T-06.

Los límites de ADR-0056 se conservan: 1.000 jobs activos, 64 IDs conocidos,
chunks de 64, frames de 64 KiB, 32 suscriptores y 64 pendientes por lector.
La consulta debe detectar exceso mediante una fila adicional, sin cargar ni
truncar silenciosamente todos los jobs. La autorización se comprueba antes de
emitir replay o snapshot; la petición no admite tokens en URL.

## Restricción de propiedad actual

`runtime`, `admission`, `resolver`, `provenance` y contratos pertenecen a la
unidad sintética cuya QA independiente sigue roja por una aserción de
recuperación tras0,35s. El diagnóstico actual es de sólo lectura. Esta
preparación no modifica esos archivos ni ejecuta otra carga temporal durante
las observaciones del caso. El diff de integración se construirá sobre su
entrega aceptada; sus pruebas no sustituyen las de T-06.
