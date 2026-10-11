# Captura privada de iteración creativa

La unidad `app.creative.recipes` implementa la captura, lectura y proyección pura
del [contrato privado de recetas](../roadmap/2026-10-10-m2-iteracion-creativa/recipe-contract-design.md),
ratificado mediante [ADR-0077](../decisiones/ADR-0077-envelope-privado-de-recetas-creativas.md).
Sigue la arquitectura de [ADR-0073](../decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md)
y la separación de autoridad CPU de [ADR-0074](../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md).

## Captura y sello

`capture_recipe(mapping)` recibe un contexto resuelto por el server. Devuelve
`CapturedRecipe`: DTO congelado, bytes canónicos UTF-8 y SHA-256. El capturador
no consulta la BD, no lee audio y no encola, ejecuta ni publica.

`capture_request(mapping_or_recipe)` produce `CapturedRequest`. Su valor tiene
exactamente `kind: creative_recipe`, `schema_version: 1`, `recipe` y
`recipe_sha256`. El caller de la integración posterior conservará este objeto
completo en `job.request`. El SHA de la receta y el SHA del envelope son hechos
distintos. No hay sidecar de parámetros que compita con la receta.

La receta conserva owner, song, job, take destino, raíz canónica, todos los
padres, assets master/manifiesto, derechos, letra histórica, selección y pins.
Las ocho operaciones son `variation_request`, `variation_audio`, `extend`,
`repaint`, `cover`, `trim`, `fade` y `crossfade`.

Los DTOs son estrictos, congelados y cerrados. Los arrays privados son tuples;
`FrozenJSON` y `FrozenJSONObject` almacenan JSON canónico como texto inmutable
y entregan copias mediante `wire`. Modificar datos originales, `model_dump()`
o una vista separada no cambia los bytes/hash capturados.

El codec usa `ensure_ascii=False`, claves ordenadas, separadores compactos y
`allow_nan=False`. No normaliza Unicode ni CRLF. Los segundos se normalizan a
float durante captura; la lectura sellada no corrige posteriormente enteros,
espacios, escapes o representaciones distintas. Los límites, rangos y
precedencias exactos están en §4.1–4.2 del contrato ratificado.

## Padres, letra y mapas

La captura valida pertenencia interna, IDs, hashes y vínculos de master,
manifiesto y derechos. La raíz es el mínimo de las raíces capturadas de los
padres; demostrar esas raíces, el DAG y la pertenencia real sigue siendo
responsabilidad del caller autorizado.

Crossfade conserva dos padres ordenados, `crossfade_a` y `crossfade_b`, con
mapas ligados a cada uno. No fuerza una sola historia textual. Los contextos
`single`, `instrumental` y `composite` conservan versiones, bindings y
declaraciones históricas. El SHA textual corresponde a los bytes exactos;
no se consulta la letra actual de Song ni se convierte `assistant` en `own`.

`section_map.kind: requested_seconds` declara intención. Sus operaciones se
comprueban contra la región, duración y operación elegidas. No son índices de
muestra ni mapas medidos. La construcción, el recibo de ejecución y la
publicación posteriores conservarán resultados efectivos vinculados al SHA;
no sustituirán la receta sellada.

Variación de petición exige el `JobRequest` efectivo completo del intento
ganador, su hash y el índice de salida elegido. Conserva params con sus tipos
JSON, task, modelo, modo y timeout. La semilla anterior es `seed + output_index`;
la nueva debe ser distinta. No reconstruye ese request desde `Take.params`.

## Selección y descriptor

Inference conserva selección local, descriptor, capacidades, parámetros y
semilla para un envío futuro. `FrozenDescriptor` es un capturador M2 aislado:
cierra los modelos públicos recursivamente y materializa sus defaults sólo
durante captura nueva. Su reader preserva bytes/hash sin insertar defaults.
`wire` y `value` devuelven vistas nuevas. No utiliza ni cambia los capturadores
o codecs privados de M1.

Los parámetros cumplen el schema exacto y cerrado de la tarea. No hay refs
externas, nombres de coordenadas inventados ni conversión implícita de audio.
El cierre incluye los objetos de uniones como `type: [object, null]`, las
referencias locales y las posiciones de schema de combinadores y arrays.
El recorrido distingue esas posiciones de los mapas de nombres y los valores
literales de `const`, `default`, `enum` y `examples`; una propiedad llamada
`properties` conserva su significado de dato. Cada schema de objeto exige
`additionalProperties: false`, sin insertar el cierre ni defaults.
Los keywords de objeto implican ese cierre cuando falta `type`. Si un tipo
explícito excluye objetos, esos keywords no exigen cierre: se conserva su
semántica Draft 2020-12 y la validación del valor contra el schema exacto.
Task/features deben estar verificadas en el snapshot. Un descriptor sintético
requiere su binding coherente, que todavía no acredita registro o autorización
runtime. CPU declara `audio.edit`, herramientas y formato; no lleva modelo,
engine, semilla, intento ganador, terminal ni execution_id ficticios.

Los pins conservan `runtime_verified`, también cuando es false. La conjunción
de derechos, entradas, letras, herramientas y modelo determina el flag
`commercial_use`; validar ese flag no acredita permisos legales o instalación.

## Proyección pura a engine `/v1`

`project_input_requirements(captured)` distingue `asset_role: master` de
`engine_role: source`. La variación de petición produce cero requisitos;
retake/extend/repaint/cover requieren el master capturado. Ambas proyecciones
rechazan CPU.

`project_engine_request(captured, attempt_id=..., inputs=(...))` valida identidad,
hash, media type y ruta relativa de cada `ResolvedRecipeInput`. Crea un
`JobRequest` nuevo con `n_outputs: 1`, el ID del intento entregado y
`output_dir: tmp/<attempt_id>`. No envía owner, song, receta, derechos privados
ni synthetic_binding al engine. El resultado mutable no comparte params con
la receta.

Roles desconocidos o repetidos, required ausentes y media types incompatibles
fallan. Un master FLAC y un descriptor WAV-only no se retaggean ni convierten.
La integración futura comprobará bytes reales, custodia, capacidad viva y el
seam de referencias M1 antes de ejecutar.

## Lectura histórica y errores

`read_recipe(bytes, schema_version=1, expected_sha256=...)` requiere hash externo
y bytes canónicos exactos. `read_request(bytes_or_mapping, expected_sha256=...)`
despacha por kind/version; una presencia parcial o versión desconocida nunca
cae al lector histórico. En bytes, el SHA esperado corresponde al payload
crudo; en mapping, corresponde al JSON canónico del mapping recibido.

Las peticiones M1 sin kind/schema_version producen `LegacyRequestView`. Conserva
claves presentes, nulls, semillas históricas grandes y raw bytes/hash cuando
existen. Su canonical_payload es una representación separada; no reemplaza el
recibo original. No rellena params, inputs o mode ni añade origin. Los readers
de PostPlan, private_context, manifiestos y song snapshots completos mantienen
su propia autoridad; esta unidad no los convierte a receta.

Se rechazan duplicados JSON, BOM, UTF-8 inválido, trailing data, NaN/Infinity,
extras y secretos. La lista de claves se compara por igualdad después de
NFKC/casefold; `tokenizer`, `max_tokens` y texto artístico «mi token» siguen
permitidos. Los namespaces reales de descriptor/schema tienen sus propias
guardas cerradas; una clave dinámica llamada descriptor no evita el veto.
PEM privado, Bearer completo y URI con userinfo se rechazan sin eco.

`RecipeError` expone `code` y `field` sanitizados. No incluye entrada, letra,
paths o repr de Pydantic en el mensaje. Los códigos privados no añaden por sí
solos endpoints ni códigos HTTP nuevos.

## Alcance de las pruebas

`uv run pytest -q apps/server/tests/test_creative_recipes.py` verifica la unidad
con contextos sintéticos CPU puros. La cobertura oficial se obtiene sobre la
ruta completa `apps/server/app/creative`, sin exclusiones. Las pruebas no abren
BD, leen archivos musicales ni ejecutan GPU, Docker, LLM o herramientas.

Esta evidencia comprueba el contrato de captura y las proyecciones puras.
Admisión transaccional, migración, construcción por muestras, recibos/custodia,
publicación, export/import y capacidades musicales reales pertenecen a unidades
posteriores. No acredita adopción, QA integral o aceptación M1/M2.


## Composición por muestras de T03 — contrato propuesto

[O1 de composición](../roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md) y [ADR-0079](../decisiones/ADR-0079-composicion-creativa-por-muestras-medidas.md), pendientes de revisión documental y QA, concretan un plan privado de construcción ligado a la receta T02. Preflight declara conversiones; el caller convierte y mide antes del cierre. Índices se resuelven una vez por primitiva y grid, con half-up y rangos semiabiertos; el render consume frames.

Full consume el buffer engine completo una vez; sus keeps de linaje quedan declarados sin verificación hasta el contraste PCM en T08. Repaint region ensambla prefijo+región medida+sufijo; extend region ensambla prefijo+región medida y descarta el sufijo antiguo. Padre100/at70/G40 produce110frames. La región/punto global pertenece al padre; la salida engine region se consume localmente desde0, también tras conversión.

Crossfade conserva dos padres y expresa convert con sus formatos y scope completos. FIX1 propone nominal_src de B convertido que puede ser vacío, separado del render/destino no vacío y con dependencia del buffer original completo. No equivale al footprint exacto de soxr; su ratificación corresponde a ROOT. T03 sólo valida facts/plan y no prueba audio, custodia, SQL, publicación ni capacidad musical. La implementación, su verificación y gates de T03 están pendientes; T02 aceptada no se modifica.

## Dependencias de producción M3

El [contrato de dependencias M3](../roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md)
registra disponibilidad por unidad, versión, fuente SHA y gate. Es una propuesta
D-12 para ROOT, bajo O1 de ADR-0080; no habilita funciones por documentación.

El recibo ROOT actual acepta T03 como compositor puro por muestras. La descripción
anterior conserva el contexto de propuesta previo a esa liberación. Render PCM,
custodia, SQL, publicación y capacidad musical siguen fuera de ese scope.
M2 permanece abierto, 3/30; M1 conserva 0/17 formal y T05 abierto. La aceptación
M3 exige cierre M2 y gates heredados. T02/T03 puros no sustituyen integración.

#### Reserva y publicación de edición CPU

CreativeRequestV1 y CompositionPlanV1 son capturas puras. Job.request conserva envelope sellado; CpuEditPlanV2 añade execution y reserva PRE-render después. audio.edit es task/handler privado server, lane CPU, contract_version2/handler_version1. Padres/modelo/seed son antecedentes. PRE-render crea job, Take queued, aristas, CPUPreRenderReservation y ejecución prepared completas en transacción. Plan/reserva no contienen PUB IDs/source/receipt; no hay FK a fila final inexistente ni hash marcador. Raíz/destino/parents/ordinal/capturas ya son reales durables antes de efectos.

Take.batch_id deriva de reservation_ref.id activo, ULID no-null de la reserva/agrupación real CPU, sin Batch ni campo duplicado en plan. Ejecución/receipt/publication binding/authority resuelven su propia reserva y agrupación; al publicar igualan batch activo. No usar NULL/grupo padre/arbitrario/ajeno/malformado ni identidad de inferencia inventada. NOT NULL/CHECK/índice y batch IDs/semántica M1 históricos se conservan.

Renderer mide fuente/render/mapas/herramientas propios. CpuEditReceiptV2 incluye reservation_id y liga hechos al plan/recipe/composition/provenance por SHA/evidencia; duración source/master viene de frames, nunca request/suma padres. Terminal running→draining fija receipt write-once; cierre real confirmed/VerifiedCpuEvidence y rehash raw acreditan source_verified. Después reservePUB crea intención/revisión finales con source_sha real NOT NULL, bindings y counters CAS completos. CpuPublicationBindingV2 leído de filas reales une paquete a esa reserva sin reescribir plan. PreparedPackageCPU exige receipt/cierre/métricas reales y CAS/no-clobber/assets+ready+committed sin promoción automática. T-07 mantiene gate real.

Retry cerrado antes de ready conserva recipe/request/parents/maps/root/job/take y toda historia; crea ordinal/ejecución/reserva/plan/receipt propios, jamás usa receipt padre/anterior. CAS retargetea juntos Take execution/hash/batch hacia nueva reserva.id; historia conserva el grupo derivado de cada reserva antigua, no igualado al batch actual. Si no hubo PUB, sigue ausente durante nuevo render; si hubo PUB fallida, historia exacta y nueva revisión sólo tras nueva fuente real. Take ready nunca rebind, tampoco batch incluso soft deleted. Lost ACK recupera IDs/counters/binding exactos; concurrent duplicate/stale rechaza atómicamente. UNKNOWN impide publicación/serving/limpieza/release y retry; ni PID retirado ni plan puro ni hash concede cierre.

Previews audio.compare son ejecución propia CPU v2 por job, sin Take/asset job/publication_intent ficticios. Contexto/recibo privado conserva A/B masters/hashes/derechos, política atenuación medible y outputs completos. Cambios de contexto invalidan acceso/caché; UNKNOWN/resultado parcial nunca se sirve. Las previews no se añaden al cierre portable como versiones musicales.

Los lectores despachan por tuple/kind/version exactos, conservan PostPlan/PreparedPackage M1 byte históricos y rechazan versiones desconocidas antes de efectos. Web M2 usa TakeV2 para historia mixta, batch CPU no-null igual a provenance.reservation_id activo; letra composite preserva bindings/historia y no atribuye alineación o duración musical sin medición. Snapshot v2 conserva autoridades CPU, batch activo y grupos propios derivados de todos ordinals sin leases/PIDs ni reescribir v1. SQL/ORM/import rechazan grupos erróneos y preservan root/maestro/DAG; M1 mantiene 409 preeffects y listado completo autorizado.
