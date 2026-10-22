# ADR-0060 · Captura write-once de procedencia antes del envío

- **Estado:** aceptada por delegación del propietario; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-09.
- **Desarrolla:** [ADR-0055](ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md).

## Decisión

Se elige O2: la reserva puede guardar la pareja de procedencia y SHA como null. El resolver conserva por separado el descriptor seleccionado y la identidad observada, en un snapshot profundamente inmutable. La primera captura válida se persiste una sola vez, después de la carga y antes de submit. No se cambia el contrato /v1 ni se añade una tabla, servicio o migración.

En GPU se verifica el acuse de load y se obtiene un Health fresco. El residente observado debe coincidir con modelo y modo seleccionados; una discrepancia conocida impide enviar. En CPU no se añade una carga por comodidad: loaded=null conserva su significado de ausencia real de observación anterior al envío. No acredita el modelo ni los controles efectivos de ejecución.

El helper construye la evidencia y el SHA fuera del writer. Dentro del writer, el server revalida propietario, canción, intento y ordinal vigentes, petición y carga exactas, cancelación, estado y pareja nullable. Una pareja idéntica es idempotente; una pareja diferente se rechaza. Las autoridades y guardas existentes del envío permanecen intactas. El descriptor no se sustituye por un catálogo posterior.

La captura incluye únicamente tareas musicales verificadas que admite CapturedProvenance. Los trabajos no musicales conservan su semántica; no reciben procedencia musical inventada. Sin autoridad configurada del digest esperado, expected_image_digest=null. El literal unknown del engine se normaliza a null; un digest conocido inválido o discrepante no se convierte en desconocido para permitir el envío.

## Recuperación y publicación

La recuperación no completa retrospectivamente un intento antiguo con datos del catálogo actual. Un reenvío confirmado como ausente conserva la captura anterior y revalida sus identidades antes del efecto. La rama submitted usa sus guardas de recuperación; no elude controles tomando únicamente una guarda preparada.

PublicationIntentRevision liga su contenido al SHA de la captura vigente y al intento ganador, su terminal e índice original. Los parámetros solicitados y la observación anterior al envío quedan separados de los controles LM/DiT y semillas efectivamente reportados. Esta decisión no incorpora un canal nuevo de evidencia efectiva ni añade image_evidence al manifiesto.

## Alternativas y límites

Capturar durante la reserva puede registrar otro residente que va a descargarse: se descarta como evidencia de la carga elegida. Un canal adicional de observación efectiva podría ampliar el diagnóstico, pero exige otra decisión y no sustituye la captura previa al envío. O2 utiliza los campos e invariantes actuales y mantiene explícito lo desconocido.

La siguiente unidad abarca provenance.py, resolver.py, admission.py, retry.py, dispatcher.py y runtime.py, con pruebas nuevas sobre SQLite real y engine de prueba declarado. Debe acreditar RED conductual de ausencia de evidencia en la frontera submit, integridad write-once, cancelación, retry/offload y recuperación, cobertura actual de cada módulo completo >=80 % sin exclusiones, revisión fresca y QA independiente. No se declara ejecutada ninguna de estas pruebas en este ADR.

No acredita una generación, la imagen de un contenedor, controles efectivos, rendimiento, derechos, calidad musical ni el cierre de T-05. El diseño estático conserva sus límites de captura posterior a primeras lecturas; el estado permanece exclusivamente en el ledger.


La compatibilidad honesta del mock se concreta en [ADR-0062](ADR-0062-evidencia-sintetica-explicita-con-binding-del-server.md): evidencia sintética explícita con binding confiado del server, sin rebajar los requisitos de pesos de la rama aprendida. Implementación y pruebas pendientes.
