# Fixtures contractuales sintéticos — versión 1

Todos los IDs, hashes de assets/pesos/herramientas, declaraciones de derechos,
modelos, semillas, mapas y textos son inventados o proceden de fixtures de prueba
del repositorio. No representan archivos musicales existentes, un usuario real,
un motor habilitado, permisos concedidos ni una ejecución instalada/verificada.
No contienen credenciales ni información personal. `runtime_verified: false`
permanece así. `verified` de un descriptor describe únicamente el escenario
contractual sintético; no habilita ese modelo en un registry de producción.

`fixture-index.json` fija SHA-256 y longitud de los 22 JSON de entrada; no se
incluye a sí mismo. Los hashes de archivos ficticios dentro de las entradas son
datos de contrato, no pruebas de existencia de audio. Los hashes del inventario
sí se verifican sobre bytes reales de estos JSON. Las recetas y envelopes son
UTF-8 canónico del codec T02; `legacy-request-seed-only.json` conserva espacios
y salto de línea históricos deliberados, con hash crudo diferente del canónico.

Las ocho operaciones son variation_request, variation_audio, extend, repaint,
cover, trim, fade y crossfade. El mapa `requested_seconds` expresa intención,
no duración medida ni fidelidad de muestras. La CPU no lleva modelo/seed/attempt
de ejecución. El origen de sus padres es antecedente. La variación conserva el
output elegido del request histórico; su proyección es pura y no se envía.

`engine-postplan-v1.json` conserva el DTO y lector histórico M1.
`manifest-v1.json` deriva del ejemplo contractual audio_take; se valida su forma,
sin crear archivos con extensión musical ni fingir verificación de audio.
`song-snapshot-v1.json` representa owner/song/job request seed-only sin takes,
assets, ejecuciones ni autoridad CPU. Se lee con `snapshots.validate` real sin
crear SQLite. Los lectores históricos no se modifican para admitir estas entradas.

El esquema nuevo describe CreativeRecipeV1 **privado**, no endpoint público ni
manifiesto v2. La versión 1 se transporta en CreativeRequestV1 o en el argumento
`schema_version` de `read_recipe`. JSON Schema expresa forma; el codec conserva
las reglas semánticas, hash, versión y relaciones. Ningún esquema sustituye
custodia, autorización, instalación, mediciones de audio, storage o QA E2E.

Congelación original: script privado `prepare.py` del recibo T04, contra snapshot
fijado. Sus fuentes y SHA están en el recibo y `additional-sources-before.json`.
FIX1 regenera únicamente el schema mediante `prepare-schema.py` del namespace
privado de corrección, desde los DTO de serialización y el descriptor cerrado.
Su mapping v1 convierte cardinalidades de arrays a `minItems`/`maxItems` y límites
numéricos a los keywords Draft 2020-12, según el tipo local del nodo. Los 22 JSON
congelados permanecen byteexactos; `recipe_schema_sha256` del índice fija el schema
actual. El recibo FIX1 conserva auditoría de todos los nodos y prueba reproducible.
