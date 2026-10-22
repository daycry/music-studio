# T-06 · Contrato de integración HTTP del stream

Decisión del orquestador bajo delegación del propietario, previa al handler.
Implementación, exportación code-first, revisión y QA todavía pendientes.
Complementa ADR-0056/0058/0065 y [integration-design.md](integration-design.md).

`GET /api/events` requiere exactamente un `X-Studio-Session-Token`. El cursor
opcional llega en un único `Last-Event-ID`, validado por la gramática vigente
`epoch:seq`, ASCII y máximo de 96 bytes. La sesión determina el owner; ningún
parámetro del cliente puede sustituir esa autoridad. No se admiten tokens,
owner ni cursor en query, cookies o headers de engines.

La query admite exclusivamente `song_id` opcional y singleton, y hasta64
`known_job_id` repetidos y distintos. Ambos tipos son ULID válidos. Se rechazan
duplicados, valores desconocidos, escapes inválidos y exceso de query antes
de materializar una colección sin límite. La query cruda tiene un máximo de
4096 bytes; permite holgadamente64 pares con IDs de26 caracteres. Ese límite
no amplía el máximo de URL del cliente. Los IDs conocidos son pistas de
reconciliación, nunca permisos ni un límite del feed dinámico.

Cada canción y job se autoriza en SQLite contra el owner y filtro vigentes
antes de replay o snapshot. IDs ausentes, ajenos, borrados o incompatibles
con el filtro producen `403 FORBIDDEN_SCOPE`, sin eco ni distinción que revele
existencia. Se conservan Host/Origin/CORS y el bootstrap local de ADR-0058.

Cambiar de filtro cancela la conexión anterior, elimina el snapshot parcial
y cursor en el cliente y abre el nuevo scope sin `Last-Event-ID`. La gramática
actual del cursor no contiene la identidad del filtro: no se afirma que el
servidor pueda detectar ese cambio sólo a partir del cursor. La pertenencia
de los datos sí se revalida siempre, incluso si el cliente reutiliza un cursor.

Errores finitos antes del status200:

| Condición | Respuesta |
|---|---|
| Query/cursor inválidos, duplicados o más de64 conocidos | 422 `INVALID_PARAMS` |
| Credencial ausente, inválida, expirada o revocada | 401 `SESSION_REQUIRED` |
| Filtro/ID sin autorización vigente | 403 `FORBIDDEN_SCOPE` |
| Registro lleno | 503 `SESSION_LIMIT` |
| Owner/DB/barrera/alta de lector no disponibles | 503 `SERVICE_UNAVAILABLE` |
| Snapshot supera1000 activos o el límite de frame permitido | 503 `SNAPSHOT_LIMIT` |

`SNAPSHOT_LIMIT` es una ampliación explícita y compatible del enum de códigos
de `ProblemDTO`; se añadirá al código, al OpenAPI generado y a sus pruebas en
el mismo cambio. No se usa todavía ni se modifica a mano el contrato canónico.
El snapshot detecta exceso mediante una fila adicional, sin truncar estados.
No se inicia el stream antes de validar autorización, límites y frames.

Tras status200, revocación, overflow, desconexión o error cierran el lector;
no se intercala ProblemJSON como si fuera un evento. La nueva petición vuelve
a validar todo. Heartbeat de15s sin ID, envío de30s y cleanup supervisado se
prueban con ASGI real. Un test in-process que almacena toda la respuesta no
acredita streaming, desconexión ni el timeout de envío.

La alta preparada en el event loop y el attach síncrono del ticket ocurren
según O1 bajo la barrera compartida con el snapshot WAL/H. No se habilita la
ruta productiva con escritores fuera de esa coordinación. La implementación
posterior necesita el inventario actualizado de todos los mutadores, incluidos
los nuevos writers CPU o de dominio antes de exponerlos.
