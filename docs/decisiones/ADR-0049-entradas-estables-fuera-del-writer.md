# ADR-0049 — Entradas estables fuera del writer de SQLite

- **Estado:** aceptada como decisión; implementación, revisión y QA pendientes
- **Fecha:** 2026-10-08
- **Decisor:** orquestador bajo delegación autónoma explícita del propietario
- **Ámbito:** M1/T04; concreta ADR-0018, ADR-0043 y ADR-0047

Las lecturas completas de audio dentro de la transacción de reserva retienen el writer de SQLite. En una llamada asíncrona también pueden bloquear el event loop. Las sondas de U1 reprodujeron ambos efectos; una entrada FLOAT estéreo de tres minutos a 48 kHz tiene unos 69 MB. La validación de sus bytes debe preceder a la reserva durable sin trasladar esa lectura al writer.

El server prepara copias propias en data/tmp/_server_inputs/<uuid>/<index>, fuera del directorio de salida del engine. Comprueba pertenencia, referencias y SHA-256 de origen; copia y vuelve a verificar los bytes de la copia antes de entrar en la transacción. La llamada asíncrona ejecuta esta preparación en un hilo. Las copias quedan de sólo lectura para el uso ordinario del estudio. Se conservan los campos y roles del contrato /v1; las rutas de inputs del payload congelado apuntan a las copias.

La transacción comprueba de nuevo estado, usuario, canción viva, dependencias, capacidad del carril, referencias de origen e identidad de las copias. Reserva job_attempt y su petición contractual exacta antes de enviar HTTP. No relee ni copia el audio dentro del writer. Las comprobaciones rápidas de identidad complementan el SHA-256 previo de la copia propia; no convierten mtime de un archivo ajeno en autoridad sobre sus bytes.

Sólo se elimina staging propio cuya ausencia de reserva durable está acreditada. Un intento preparado o posiblemente enviado conserva sus inputs para reconciliación y reanudación. Una excepción al observar el commit no demuestra rollback: hay que resolver su disposición o conservar las copias. La limpieza posterior requiere identidad y pertenencia verificadas; nunca borra el directorio padre ni temporales desconocidos. Su integración en recuperación y cancelación pertenece a U2 y continúa pendiente.

Se eligió copiar entradas porque conserva bytes concretos sin mantener un hash largo bajo el writer. Mantener la lectura en la transacción retiene el bloqueo observado; depender exclusivamente de locks específicos de Windows no sirve como mecanismo del server Docker Linux. La copia añade disco temporal y una lectura adicional antes de reservar, que deberán medirse y limitarse.

Esta decisión no añade tablas, campos contractuales ni infraestructura. Los engines sólo leen inputs y escriben salida cruda en data/tmp/<attempt_id>/. No declara aceptación de U1/U2/T04, cleanup integrado, prueba Linux ni resistencia ante un proceso comprometido que opera con los permisos del propio server. La revisión debe comprobar reserva concurrente, cambio de origen, writer disponible durante hashing, event loop activo y conservación de copias cuando el resultado del commit es desconocido.
