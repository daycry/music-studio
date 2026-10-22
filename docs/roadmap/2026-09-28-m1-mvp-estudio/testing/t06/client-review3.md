# Cliente de eventos — revisión3

Las cuatro lentes A/B/C/D finalizaron sin gaps pendientes. Este es el tercer
intento del componente, con los veredictos anteriores conservados. Los
revisores son actores nativos existentes, independientes del productor; sus
contextos se reutilizan y no se presentan como contextos vacíos. Realizaron
lectura estática y cotejo de metadatos; no ejecutaron la QA.

| Gap | Disposición | Evidencia actual |
|---|---|---|
| CLIENT-01, cursor reentrante | Corregido | `event-reducer.ts`: confirmación tras callback sólo con revisión vigente. |
| CLIENT-02, cancelación pendiente | Corregido bajo contrato UNKNOWN | `event-session.ts`: espera acotada y promesa retenida; halt visible sin reapertura automática. |
| CLIENT-03, snapshot ignorado | Corregido | `events.ts`: consumidor obligatorio antes de I/O. |
| CLIENT-04, agotamiento de sesiones | Corregido | Propietario único entre scopes, revocación dedicada finita;204 confirmado,401 inactivo y fallo desconocido. |
| CLIENT-05, último401 sin halt | Corregido | `events.ts:77`: halt antes de renovar en el último intento. RED conductual con/sin consumidor de error. |
| CLIENT-06, waiter compartido | Corregido | `event-session.ts:129`: waiter por lectura, retirada de timer/listener en finally. RED de65.537 registros frente a máximo1. |

El contador de CLIENT-06 mide inscripciones `.then`, no heap, GC, bytes
retenidos ni latencia. La evidencia del productor contiene222 pruebas de13
suites, lint y TypeScript exit0; cuatro archivos completos superan94% de
cobertura combinada y no excluyen código. Root comprobó fuentes, preimágenes,
protegidos e inventario original. Los mocks de fetch/ReadableStream no prueban
el registro HTTP ni la ejecución en navegador.

[Fusión privada](../../../../../.cache/dev-cycle/m1/t06-fetch-client-review3/root-adjudication.json)
y cuatro salidas nativas originales en el mismo directorio. Se libera una
QA técnica CPU independiente sobre las fuentes congeladas. T-06 sigue
abierta: HTTP, todos los escritores/WAL, Docker y E2E no se acreditan aquí.
