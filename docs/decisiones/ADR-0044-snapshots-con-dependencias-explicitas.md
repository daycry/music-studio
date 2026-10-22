# ADR-0044 — Snapshots con dependencias explícitas y publicación acotada

- **Estado:** aceptada; implementación, revisión y QA pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación autónoma del propietario
- **Ámbito:** M1/T-02, R02-03 y R02-07; complementa ADR-0041

Un personaje global o la portada de una colección puede utilizar un artwork perteneciente a otra canción. Es una referencia legal del mismo usuario. El snapshot actual incorpora esa canción y todos sus hijos, pero después rechaza el resultado porque exige una única canción. Además, cada commit proyecta toda la biblioteca repetidamente. La solución debe conservar esas referencias sin convertir una dependencia en otro proyecto completo.

Se compararon dependencias explícitas, normalización de recursos globales y un bundle de proyectos completos. Se elige **una raíz completa y un cierre dirigido de dependencias explícitas**. Normalizar recursos alteraría identidad o pertenencia; exportar todos los proyectos alcanzados arrastraría contenido no solicitado. Ambas posibilidades quedan para iniciativas distintas.

`song.json` conserva `version=1`, `song_id` y `rows`. Añade un campo opcional `dependencies`, con `rows` y `provenance`; su ausencia equivale a conjuntos vacíos para los archivos anteriores. `rows.song` contiene exactamente la raíz. Una identidad `(table, id)` aparece una sola vez entre ambos conjuntos. Se conservan los IDs, propietarios, fechas, borrados e historia. Las filas de soporte pertenecientes a otras canciones se declaran en dependencias; los recursos globales necesarios conservan su naturaleza global.

El cierre incluye toda la historia de la raíz y las unidades globales necesarias, destinos de FK, sujetos de assets, padres de linaje y dependencias de jobs. Alcanzar una canción como soporte cierra su fila y sus selecciones explícitas, pero no enumera sus otros hijos. Alcanzar un vídeo exige la unidad necesaria para validar su timeline; alcanzar un personaje incluye sus referencias y assets. No se incorporan consumidores inversos ajenos ni se interpretan strings arbitrarios de JSON como relaciones. Los ciclos estructurales legales terminan mediante identidades visitadas; los grafos de linaje y jobs siguen siendo DAG.

La procedencia identifica `source_root_id`, `owner_id` y hashes por identidad de fila. El hash usa JSON canónico UTF-8, claves ordenadas, separadores compactos y números finitos, con normalización tipada de la representación de SQLite. No equivale a autoría ni al hash de un medio. El validador recalcula cierre y hashes; las filas externas sobrantes, el propietario distinto y las referencias incompletas se rechazan.

SQLite distingue de forma durable una canción de soporte mediante la columna aditiva `song.is_dependency_only`, falsa por defecto. Una canción importada sólo como soporte no aparece como proyecto completo, no entra en FTS ni se despacha para generación. Su contenido no se modifica mediante acciones ordinarias de proyecto. Puede promoverse mediante la importación validada del proyecto completo con IDs y filas compatibles. Una canción completa existente nunca se degrada. Esta marca es metadato local de persistencia y se excluye de las filas canónicas exportadas.

La importación valida todo antes de insertar. Un ID existente exige igualdad canónica; una divergencia, path ocupado por otros bytes o propietario distinto aborta la transacción. Los IDs no se remapean. Una base nueva puede inicializarse con el usuario del archivo antes de sembrar el usuario local; una base poblada con otro usuario declara conflicto. Los ciclos de selecciones se insertan por fases con FK diferidas y validación final. JSON permite restauración estructural; un paquete portable de medios exige además los bytes, hashes y rutas originales confinadas, sin sobrescribir manifiestos ni seguir symlinks. T02 no afirma haber implementado el export ZIP de medios.

La publicación usa consultas por IDs y relaciones indexadas dentro de una vista de lectura consistente. No materializa la biblioteca completa para cambiar la valoración de un take. La invalidación durable registra las raíces afectadas, también ante SQL/Core/bulk, movimientos OLD/NEW y recursos globales compartidos. Se añaden `song.snapshot_dirty` y `song.snapshot_generation` como metadatos locales; sólo se publica lo pendiente. El mecanismo transaccional de invalidación debe incluir todos los consumidores y evitar los ajenos, con pruebas de conteo y planes de consulta.

El publicador compara la generación capturada antes de limpiar dirty. Un cambio concurrente o una publicación fallida conserva la reparación pendiente. El arranque repara de forma recuperable y un fallo individual no impide otras canciones ni el arranque del backend. No se promete atomicidad entre SQLite y el filesystem: SQLite sigue siendo la fuente de verdad y el reemplazo del JSON es atómico por archivo.

Los metadatos locales se añaden mediante migración posterior al baseline inicial; no se reescribe retrospectivamente su evidencia. Las dos copias del contrato se actualizan juntas y se conservan los casos anteriores. La implementación debe probar ambos ejemplos de referencias compartidas, restauración, promoción, conflictos, historia, ciclos permitidos, invalidación por SQL y ausencia de escaneos de toda la biblioteca por una modificación local. Revisión2 y QA independientes preceden la aceptación técnica de T02.


La [QA técnica de T02](../roadmap/2026-09-28-m1-mvp-estudio/testing/t02/qa4-report.md) y la revisión4 son conformes sobre el baseline0004 congelado. Integración Git, verificación global M1 y M-03 real siguen pendientes. El registro de estados permanece en tasks.md.
