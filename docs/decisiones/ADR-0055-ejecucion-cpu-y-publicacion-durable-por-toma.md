# ADR-0055 · Ejecución CPU y publicación durable por toma

- **Estado:** aceptada bajo delegación autónoma del propietario; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-08.
- **Relacionadas:** [ADR-0053](ADR-0053-postproceso-cpu-portable-en-el-server.md), [ADR-0043](ADR-0043-identidad-durable-de-intentos.md), [ADR-0049](ADR-0049-entradas-estables-fuera-del-writer.md) y [ADR-0017](ADR-0017-postproceso-y-manifiesto-en-el-server.md).

## Contexto y alternativas

`post.audio` es trabajo local del server, sin modelo ni terminal de engine propios. La cadena vigente contiene una generación, un post agregado y un análisis por toma. Un audio inválido debe poder fallar sin perder las variantes válidas ni dejar su análisis esperando indefinidamente.

Se compararon mantener el post agregado con resultados por toma (P1), crear un post por toma y un grupo adicional (P2), y hacer fallar todo el post cuando falla una variante (P3). P1 conserva IDs, solicitudes y dependencias de la cadena existente. P2 añade complejidad de coordinación y compatibilidad; P3 necesita excepciones que confunden el resultado de la ejecución con el de las tomas. Se elige P1.

## Decisión

El padre publica y confirma cada toma independientemente. Para el post nuevo, `succeeded` significa que todos los índices solicitados tienen resultado durable: todas listas, resultado mixto o todas fallidas. No certifica la calidad musical. Un fallo sistémico que impide determinar esos resultados mantiene el trabajo fallido o interrumpido. La cancelación conserva las tomas ya confirmadas y afecta a las pendientes.

Se añaden, mediante la siguiente migración aditiva, `cpu_execution`, `publication_intent` y `publication_intent_revision`. No se reescriben las migraciones 0001–0005. Una ejecución local tiene ordinal único por job, revisión CAS, plan inmutable con SHA y resultado; nunca comparte un ordinal con un `JobAttempt` de engine. Una intención tiene identidad única por toma, revisión CAS y una revisión de contenido activa. El historial de contenido es inmutable y vincula propietario, canción, generación, intento ganador, ordinal, secuencia y SHA terminal, índice global original, semilla y SHA de procedencia. Sólo una toma fallida o cancelada sin publicación puede adoptar una revisión nueva; una toma lista o un paquete renombrado/confirmado no se sobrescribe.

Los estados de ejecución son `prepared`, `running`, `draining`, `interrupted`, `finished`, `failed` y `cancelled`. Los de intención son `reserved`, `prepared`, `renamed`, `committed`, `failed`, `cancelled` y `quarantined`. Los cambios exigen autoridad y revisión vigentes. La identidad musical estable vive en la raíz; la procedencia y el paquete de cada intento viven en su revisión inmutable. Se evita una unicidad global del intento/índice que impida repetir una publicación fallida sobre la misma salida: la unicidad del contenido es `(intent_id, generation_job_id, winning_attempt_id, output_index)`. No se impone una nueva unicidad global de assets que invalide bibliotecas antiguas.

`JobAttempt` recibe procedencia y SHA opcionales para compatibilidad histórica; `Take` recibe `error_code` opcional. La procedencia nueva congela, antes del envío y fuera del writer, el descriptor confiable seleccionado, la identidad observada del engine y las opciones exactas de carga. No contiene tokens ni secretos. Un intento antiguo sin esa evidencia no habilita una publicación nueva (`PROVENANCE_MISSING`); las tomas ya listas se conservan. Un digest desconocido se representa como `pipeline.image_digest=null`, ya permitido en el manifiesto. El digest configurado esperado y el observado son autoridades distintas; una discrepancia acreditada bloquea la publicación. No se amplía ahora el manifiesto con `image_evidence`: esa extensión opcional puede abordarse en la unidad de procedencia si resulta necesaria.

Los snapshots añaden las tablas como propiedades opcionales y conservan el formato histórico. Incluyen historial y causalidad; excluyen epoch del supervisor, token de lease, identidad de proceso y estado operativo de limpieza. La copia SQLite conserva esos campos locales. Restaurar un snapshot no reactiva un proceso ni reutiliza su lease; las ejecuciones activas pasan por reconciliación como interrumpidas con custodia desconocida. Los validadores ORM y SQL, pertenencia, invalidación, cierre de dependencias y restauración deben contemplar las tablas nuevas.

El cómputo sigue en el hijo propio sin SQLite de ADR-0053. Comparte los dos slots CPU y el orden/paginación del scheduler con los engines CPU; funciona con el catálogo de backends vacío. Cada ejecución procesa sus variantes secuencialmente. Un slot y su staging se retienen mientras no se confirme la terminación del grupo propio, incluido FFmpeg. Una captura de PID, `CREATE_NEW_PROCESS_GROUP` o la muerte del padre no bastan como acreditación de limpieza.

El staging y el destino están en el mismo filesystem. El padre prepara y valida un paquete cerrado con manifiesto inmutable que declara rutas finales; un mapping privado fijo resuelve esas rutas a staging antes del rename. No se acepta un esquema ni un mapping proporcionados por el llamador. El rename por toma es no-clobber y se serializa con una revalidación breve de la autoridad SQLite. Los hashes y el cómputo quedan fuera del writer. Después, assets exactos, toma lista e intención confirmada se guardan en una transacción SQLite. La intención permite reconciliar cada ventana entre archivos y BD; no se afirma atomicidad entre ambas. Destinos ajenos se ponen en conflicto/cuarentena sin borrar ni sobrescribir. Los snapshots se publican tras el commit mediante el mecanismo dirty/CAS existente.

Sólo `audio.beats`, con su arista exacta y una toma lista cuya intención está confirmada, puede empezar antes de terminar el post agregado. Los beats de una toma fallida terminan con `TAKE_POST_FAILED` sin inventar un intento de engine; se conserva la compatibilidad legacy comprobada. El rol de dominio `master` se mapea a `audio` cuando lo declara el descriptor verificado, o se mantiene `master` si ése es su rol contractual. Resolve y reserve usan el mismo mapping.

Una unidad posterior añade `analysis_import`, única por intento fuente, para materializar y reintentar finitamente un análisis sin reenviar un engine que ya terminó. `Analysis` recibe causalidad opcional para legacy y obligatoria en las escrituras nuevas: intento, SHA del artefacto, asset master y secuencia terminal. El commit del análisis precede a `analysis.ready`; el terminal del engine no se falsea para representar un error de importación.

## Secuencia y verificación

La primera unidad U2a implementa sólo contrato, tablas/migración, invariantes y snapshots. No incluye procesos, publicación filesystem, FFmpeg, integración del dispatcher ni envío de engines. La capacidad CPU2 y el runtime se integran y verifican después; una prueba de tablas no acredita reservas concurrentes reales del scheduler.

Las unidades siguientes cubren captura de procedencia, roles/dependencias, custodia nativa del hijo, publicación y reconciliación, análisis y runtime. Deben probar el caso válido/inválido/válido con índices y semillas originales, cancelación parcial, retry sólo fallido con historial, replay y cada ventana de crash, catálogo vacío y concurrencia global CPU2. Se conservan TDD, cobertura de cada módulo completo cambiado ≥80 % sin exclusiones, revisión fresca y QA independiente. Docker Linux, E2E, derechos y calidad musical siguen como gates propios; T-05 y M1 permanecen abiertos.


## Concreción de la captura

[ADR-0060](ADR-0060-captura-write-once-de-procedencia-antes-del-envio.md) fija la captura write-once tras load y Health fresco, antes de submit. La reserva nullable no acredita evidencia; recuperación y publicación conservan el snapshot seleccionado y su SHA, sin backfill de intentos antiguos ni inferencia de controles efectivos. Implementación y pruebas pendientes.


La compatibilidad honesta del mock se concreta en [ADR-0062](ADR-0062-evidencia-sintetica-explicita-con-binding-del-server.md): evidencia sintética explícita con binding confiado del server, sin rebajar los requisitos de pesos de la rama aprendida. Implementación y pruebas pendientes.
