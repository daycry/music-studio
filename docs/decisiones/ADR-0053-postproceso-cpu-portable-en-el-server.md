# ADR-0053 · Post-proceso CPU portable y ejecución propia del server

- **Estado:** aceptada bajo delegación autónoma del propietario; implementación y verificación pendientes.
- **Fecha:** 2026-10-08.
- **Relacionadas:** [ADR-0017](ADR-0017-postproceso-y-manifiesto-en-el-server.md), [ADR-0035](ADR-0035-despliegue-docker-y-ollama-wsl.md) y [ADR-0043](ADR-0043-identidad-durable-de-intentos.md).

## Contexto

El paquete `audio-post` obtiene el esquema y el límite de sus rutas desde la ubicación del código. Esa ubicación cambia al instalar una wheel y no representa el directorio de datos montado en el server. Además, `post.audio` no es una tarea de un engine: no tiene modelo ni terminal `/v1` propios. El dispatcher todavía omite esa tarea.

La inspección de T-05 compara ejecución en threads, cómputo en un hijo propio y un worker supervisor independiente. La cola ya dispone de coordinación, pero sus pruebas de post-proceso usan resultados sintéticos y no acreditan el worker real.

## Decisión

Se elige cómputo CPU en un proceso hijo propio del server, sin acceso a SQLite; el padre conserva la autoridad para validar, publicar y escribir en la base de datos. Su ocupación comparte los dos slots CPU de la cola. La cancelación debe acreditar la terminación del grupo propio, incluido FFmpeg, antes de liberar el slot o limpiar archivos. No se añade un servicio ni un engine ficticio.

La primera unidad, independiente de esa integración, hace portable `audio-post`:

- `process_audio` acepta un límite de datos explícito opcional; las llamadas actuales conservan su comportamiento. El server proporcionará el directorio del proyecto montado en Docker. Fuente y destino se validan antes de leer, crear o transcodificar; no se autorizan destinos ajenos mediante autodetección del paquete.
- El esquema de manifiesto se incluye como recurso del paquete, byte idéntico al contrato canónico. Un test verifica su igualdad y la disponibilidad en wheel y sdist fuera del checkout. El llamador no proporciona un esquema alternativo.
- Se mantienen el algoritmo de audio, las salidas, la validación y la creación inmutable del manifiesto. No se cambian las dependencias, los locks ni el contrato `/v1` en esta unidad.

La ejecución local durable y su intención de publicación tendrán un contrato tipado propio; no simulan un `JobAttempt` de engine con un modelo o descriptor inventados. Sus campos y migración aditiva se concretarán antes de implementarlos. La publicación entre archivos y SQLite necesita reconciliación de sus ventanas de fallo; un rename no se presenta como transacción única entre ambas autoridades.

## Verificación y trabajo pendiente

La unidad inicial debe demostrar rechazo de escapes y enlaces antes de efectos, post-proceso real con la herramienta fijada existente, compatibilidad de llamadas y recursos instalados. Requiere TDD, revisión fresca y QA independiente. Una prueba Windows o de wheel no acredita el despliegue Docker.

Quedan pendientes el pin y la licencia de FFmpeg Linux, la procedencia durable del intento ganador, el mapeo del asset `master` al rol contractual `audio` para beats, la publicación recuperable de variantes y la integración en el dispatcher. T-05 sigue abierta hasta cumplir sus criterios completos; tampoco se cierra T-04, M1 ni la aceptación musical.
