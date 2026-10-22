# ADR-0062 · Evidencia sintética explícita con binding del server

- **Estado:** aceptada por delegación del propietario; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-09.
- **Desarrolla:** [ADR-0060](ADR-0060-captura-write-once-de-procedencia-antes-del-envio.md), [ADR-0055](ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md) y el avance con mock de [ADR-0037](ADR-0037-avance-tecnico-condicionado.md).

## Decisión

La procedencia aprendida mantiene su requisito de pesos seguros fijados y hashes válidos. Se añade una variante privada explícita de evidencia sintética, que declara ausencia de entrenamiento y pesos. No se inventan referencias de safetensors ni se presenta una ejecución del mock como inferencia de un modelo entrenado.

La variante sintética sólo se admite mediante un registro inmutable propiedad del server, construido desde composición/configuración confiadas antes de observar el catálogo. Liga el backend configurado, origen exacto, identidad contractual esperada y fingerprint canónico del descriptor y de la implementación sintética declarada. Una familia, URL parecida, class name, hash o flag recibidos en JSON no conceden autoridad. La selección, la captura durable y el reenvío cotejan el registro; clasificación y binding forman parte del SHA conservado.

El producto reconoce el descriptor real de engine-mock sin modificarlo para fingir pesos. Su origen y configuración deben quedar ligados explícitamente en la composición del server. La evidencia de fuente/build declarada no prueba por sí sola el código que ejecutó un contenedor ni un digest de imagen. Sin autoridad configurada expected_image_digest=null; reported unknown=null. Un digest conocido inválido o discrepante sigue rechazado, también para mock.

La rama aprendida es el default compatible con el JSON histórico. La selección de rama es explícita y validada: una unión permisiva de descriptores no decide por sí sola la confianza. No se modifica /v1 ni la DDL. Los intentos legacy con evidencia null no se reconstruyen desde un catálogo posterior.

## Fixtures y alcance

Los catálogos de pruebas GPU son variantes sintéticas declaradas de pruebas, distintas del mock CPU de producto. Su binding se registra en composición de test antes de mutaciones, sin exportarlo a configuración de producto ni descubrirlo automáticamente del catálogo mutable. Se conserva bf16/offload/VRAM/task/request y las condiciones negativas originales.

El marcador de digest synthetic se sustituye por unknown sólo donde el fixture carece de digest observado. Los dobles de load positivos registran y reportan el residente correspondiente al ACK real que simulan; busy, foreign y unload_lie conservan sus diferencias. Las pruebas positivas de envío/recuperación preparan una captura válida antes del escenario; sus aserciones no se convierten en rechazos para ocultar una regresión. No se cambian parámetros, timers, query bounds ni validaciones.

El primer RED usa el descriptor de la función real engine_mock.descriptor y SQLite: su captura legítima debe fallar antes de implementar la variante. Después se prueban mock sin binding, suplantación, descriptor/origen/build/identidad cambiados, learned weights vacíos, digest inválido y write-once. Deben preservarse los contratos anteriores de procedencia aprendida y los 54 tests nuevos ya escritos.

[ADR-0066](ADR-0066-sincronizacion-con-el-submit-real-en-prueba-de-recuperacion.md)
concreta una excepción posterior, probada y acotada: la espera fija de0,35s
del caso de acuse perdido se sustituye por observación del submit real con
presupuesto finito de prueba. No cambia sus cuatro aserciones, otros timers,
el runtime ni el plazo de10s del parámetro801; requiere regresión, revisión y QA.

La publicación real del WAV y su manifiesto queda como gate de la unidad de publicación. No se sustituye por un diccionario fabricado. Cobertura actual de cada módulo completo >=80 % sin exclusiones, revisión fresca y QA independiente se mantienen. Este ADR no acredita una generación, publicación, controles LM/DiT efectivos, calidad musical ni el cierre de T-05.


## Composición concretada antes de implementar

El server empaqueta una receta pura del descriptor CPU de engine-mock y los pins de fuente declarados. No importa el módulo de engine ni sus dependencias. Al construir sus propios backends HTTP, sólo registra esa receta para el origen configurado exacto `mock=http://engine-mock:8199`, antes del catálogo. La receta fija descriptor, identidad contractual y build; el mapping no concede permiso por sí solo. Los overrides de backend de pruebas requieren un registro explícito construido desde sus variantes declaradas.

El registro conserva referencias fuertes al objeto backend exacto y leases por identidad; coteja origen, descriptor y binding en selección, captura/CAS y reenvío. Tras reinicio, rebind compara la evidencia durable con la receta confiada recompuesta, nunca crea autoridad desde la fila recibida. Los pins describen fuente declarada: no prueban la imagen realmente ejecutada ni sustituyen un digest observado.

La rama learned omite clasificación y binding nuevos al serializar, incluso dentro de PostPlan, para conservar exactamente el JSON canónico y SHA históricos. La rama synthetic incorpora campos explícitos cerrados y acotados. Un validator elige la rama antes de validar el descriptor; una unión por ensayo no decide autoridad. La paridad con la función real del mock y el roundtrip/SHA learned anteriores requieren pruebas nuevas.

La unidad propuesta comprende `synthetic_registry.py`, contratos privados, provenance, resolver, admission y runtime. Retry y dispatcher mantienen sus helpers actuales. Los fixtures se adaptan mediante composición declarada antes de las mutaciones negativas, con assertions, parámetros y plazos conservados. Implementación, revisión, QA y publicación real siguen pendientes.
