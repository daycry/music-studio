---
id: ADR-0077
titulo: Envelope privado versionado para recetas creativas
estado: aceptada
fecha: 2026-10-11
iniciativa: m2-iteracion-creativa
design: ../roadmap/2026-10-10-m2-iteracion-creativa/recipe-contract-design.md
autoridad: ROOT bajo delegación del propietario; ratificación documental tras revisión A+B intento2 y QA18/18, 2026-10-11.
namespace: contrato privado del server, documentación canónica
---

# ADR-0077 · Envelope privado de recetas creativas

## Contexto

ADR-0073 captura recetas privadas en job.request. ADR-0074 preserva historia de inferencia y distingue CPU autónomo. Sus nombres/campos nuevos deben concretarse antes del RED.

Las peticiones M1 no son recetas versionadas. Resolver admite un conjunto cerrado de claves de dominio; JobAttempt conserva separadamente la petición efectiva del engine. Añadir un sidecar duplicaría params/inputs y su autoridad.

## Decisión

Los jobs creativos nuevos guardan exclusivamente CreativeRequestV1: kind=creative_recipe, schema_version=1, recipe y recipe_sha256. La receta tipada constituye la única autoridad privada de selección, padres, letra, derechos, intenciones de mapas y pins.

La captura realiza una copia validada y conserva bytes JSON canónicos/hash inmutables. DTOs y accessors no exponen aliases mutables. Readers nuevos despachan por versión y rechazan versiones desconocidas; no convierten M1 a receta nueva.

FrozenDescriptor M2 usa el modelo público y guardas por namespace. No importa ni cambia los capturadores, guardas o codecs privados M1. Materializa defaults públicos una vez al capturar datos nuevos; al leer conserva los bytes y SHA sellados. Los nombres token/tokenizer/max_tokens/token_budget declarados en schema permanecen permitidos; una credencial transportada en params sigue prohibida.

Las ocho operaciones cerradas son variation_request, variation_audio, extend, repaint, cover, trim, fade y crossfade. Inference usa selección local y params cerrados por descriptor; CPU declara task privada audio.edit y herramientas, sin modelo/seed/engine/attempt/terminal/execution fingidos. Una receta por take en esta versión.

Las letras conservan IDs, texto/hash exactos y declaración ya registrada. Crossfade conserva ambos padres, roles/mapas y letras históricas. Un contexto compuesto no fuerza una única LyricsVersion ficticia. La receta captura intenciones y antecedentes inmutables. El plan resuelve muestras; la autoridad/recibo de ejecución conserva mapa medido y duración vinculados al hash de receta. Paquete/manifiesto y linaje final reflejan esos resultados en su fase apropiada. No reescribir receta sellada ni manifiestos emitidos, conforme a Constitución §2. No se concreta aquí el schema del plan/recibo CPU.

La proyección pura a JobRequest recibe attempt_id e inputs ya resueltos por el server. Produce el /v1 actual sin datos privados de receta. Identifica separadamente asset_role=master y engine_role=source; la integración futura debe adaptar/verificar ese seam de referencias.

Selección y proyección comprueban roles únicos, ausencia de roles desconocidos, required completos y media_types exactos frente a task.inputs. Variation_request sin inputs exige que no haya required. Un master FLAC con descriptor WAV-only se rechaza; no se convierte, retaggea ni cambia su hash implícitamente. La conversión futura requiere su plan real fuera T02. Esa coherencia de snapshot no acredita capacidad viva, autorización sintética, archivos ni custodia runtime.

El reader de job.request M1 devuelve una vista inmutable de las claves presentes, raw bytes/hash cuando existen y una representación canónica separada. No rellena params/inputs/mode/seed, agrega origin ni altera snapshots, planes o recibos emitidos.

## Alternativas descartadas

- **O2: sidecar creative_recipe en request M1.** Duplica los parámetros y obliga a elegir entre dos autoridades discrepantes.
- **O3: tabla/registro separado de recetas.** Añade persistencia y reconciliación fuera T02 y de la captura ya fijada por ADR-0073.

No se reabren O2 global de ADR-0073 ni O1 de representación CPU de ADR-0074. La versión privada1 no cambia manifest/song CPU2 ni engine/v1.

## Consecuencias

T02 puede implementar captura/readers/validación/proyecciones puras sin SQL, admisión, procesos ni render. T04 exportará el schema desde código; T06 integrará envelope y referencias. Los planes/recibos/publicación CPU pertenecen a sus unidades posteriores.

Los hashes prueban integridad de captura. No prueban derechos legales, instalación de tools, autorización sintética, resultado o custodia. Los flags no verificados se conservan honestamente; la integración aplica sus gates antes de cualquier ejecución.

ROOT comprobó la numeración e incorporó ADR-0077, el índice y los documentos afectados después de revisión/QA. La preparación original había observado ADR-0076 como último número.

## Estado

`aceptada` — contrato O1 ratificado por ROOT el2026-10-11 bajo delegación, tras revisión A+B intento2 sin gaps y QA documental18/18/gate0. Índice y documentos afectados sincronizados. No acredita implementación ni aceptación T02/M1/M2.
