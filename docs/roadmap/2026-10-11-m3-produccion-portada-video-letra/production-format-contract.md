---
documento: production-format-contract
titulo: "Formatos multiversión y cierre portable M3 — D-04"
estado: aprobado
fecha: 2026-10-11
spec: spec.md
plan: improvement-plan.md
diseno_padre: design.md
opcion_elegida: PF-O1
validacion: "ROOT, por delegación explícita del propietario, 2026-10-11; elección arquitectónica, sin aceptación de producto"
adopcion: pendiente de revisión, QA documental y CAS de ROOT
adr: "candidato específico sin número en §7; reserva/adopción exclusivas de ROOT antes de schemas/código dependiente"
generacion:
  fuente: estimado
  tokens_reales: null
  eur: null
  nota: "Sin transcripción atribuible ni medidor liberado en el snapshot determinista. No se inventan consumos."
---

# Contrato de formatos multiversión y cierre portable — D-04

La opción PF-O1 está elegida por ROOT bajo delegación. Este documento es su candidato de diseño contractual: no declara lectores implementados, paquetes ejecutados ni aceptación audiovisual. El único archivo nuevo del actor está dentro del snapshot privado. ROOT controla canon, ledger, ADR, CAS y Git. **TDD n/a: prosa y validación documental; funciones M3 implementadas: 0.**

## 1. Contexto, fuentes y restricciones

T-04 concreta formatos y lectores por los siete sujetos de D-02 y el cierre de CA-12/13/18/26/36/38/39/48. D-02 y D-03 permanecen iguales, incluido FIX1 de `seal_kind`. El diseño padre O1 mantiene derivados tipados en la cola existente y escena N0 offline. La especificación está aprobada; esta elección no reabre esa arquitectura.

### Corte determinista comprobado

| Fuente relativa al snapshot | SHA-256 / hecho relevante |
|---|---|
| `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-request-contract.md` | `94e4c84771084b469bca1064dee78595930d075ed31ef13877166bed54eeb530`; 19 parejas, 7 sujetos, recipe/receipt cerrados, privacidad y autoridad por resultado |
| `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-data-contract.md` | `ca094b156a538467b495804899e5a21aff917113b44728df9ab88fbf92e76f13`; 40 tablas propuestas, 11 sellos internos, G01–G14, `root.kind` intacto |
| `docs/decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md` | `0174e9cc195c8c784b909abfe730ed60bcb593983dc525b74b25299a285b5ffd`; aceptada, CPUv2/SongCPUv2, historia inmutable, API M1 conservada |
| `packages/audio-post/audio_post/manifest.py` | `b646e71e60ced32d7d7bcf2a54fe5d07b4f1d9cced4f1f989cb118f4c362a0b8`; `SCHEMA` v1, `_validate` y `verify_manifest`, paths seguros y privacidad |
| `apps/server/app/snapshots.py` | `61189b40618a86bdaf7cd0266ab565112b55dc2de053875925c4567fff8c46f4`; `_project` emite version1, tablas/cierre y validación timeline v1 |
| `packages/contracts/manifest-v1.schema.json` | `13d837fe3ecae22a6b3b3bdea66de8599e0b5fe2ce49fc08ec05457f5f9b9224`; requiere engine/seed, kind cerrado, no familia Analysis/import/backup |
| `packages/contracts/song-v1.schema.json` | `c84b8c4baa8698931ce4590bf81b6cef1fb20ecbdcf1e1447ec94860bae5a2f1`; filas históricas, Take con modelo/seed |
| `packages/contracts/timeline-v1.schema.json` | `d85666a0dbb7f9e67a6d7442d2e44d6b971ca9584eb424941b6330e582948660`; montaje shots/texto, no escena N0 ni binding audio efectivo |
| `apps/server/tests/fixtures/creative/fixture-index.json` | `7b20e03ea12ac5a1874ef817b61c0ecee38810841bef602d4b554a924a57725c`; ejemplos sintéticos, explícitamente sin autoridad/custodia/audio ejecutado |
| `apps/server/tests/fixtures/creative/manifest-v1.json` | `f86b3fd6e75ea970e90ca65090b6bf9ed3e6f8b1b1c0ccef03b03cd5c5dfdc97`; 1351 bytes, golden v1 histórico del corte |
| `apps/server/tests/fixtures/creative/song-snapshot-v1.json` | `65b3a58d8f9b0531fe1ca02556759bf08cb61f1b343b1376e68e75a4adaf08fa`; 1491 bytes, golden Songv1 sintético |

El manifiesto de lectura completo es `release-root.receipt.json.snapshot_sha256`: 128 fuentes. La comparación SHA anterior a la escritura dio 128/128 iguales, cero diferencias. No se consultó checkout vivo como contexto, memoria externa, internet, modelos ni servicios. Las fuentes v2 de publicación no están presentes como schemas/runtime en este corte: ADR-0074 establece su frontera normativa; no se atribuye implementación ni un golden v2 ejecutado inexistente.

Los nombres de lectores siguientes son **nombres finales propuestos para código futuro**, no símbolos presentes. Todo registro requiere código/schema/golden/SHA adoptados conjuntamente, mediante contratos code-first. Tener un nombre, versión o hash aquí no habilita un reader o capacidad. Gates D-05/06/07/08/09/11/12 mantienen su ámbito. La concreción D-04 no reemplaza sus mediciones, cuotas de paquete, admisión o publicación física.

## 2. Opciones comparadas

### PF-O1 — Familias independientes, lectores exactos y originales conservados

Mantener manifiesto1 de inferencia, CPUv2 y SongCPUv2 de ADR-0074 como familias cerradas. Los sujetos M3 que no caben en ellas emplean `ProductionArtifact1`, siete ramas de lectura cerradas. El envelope refiere capturas D-02/D-03, manifiestos originales y medios; no contiene JSON libre. TimelineV2 representa N0; el cierre portable conserva cada original junto a su proyección local explícita cuando sea necesaria.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: registro multiversión y varias ramas; cada una coincide con un sujeto real |
| Riesgo | Medio: falta de reader o dependencia; falla cerrada antes de efectos |
| Coste relativo | L: schemas/readers/goldens por familia, sin cifras de horas |
| Reversibilidad | Alta para historia: lectores y originales se conservan; retirar emisión nueva no borra datos |

### PF-O2 — Nuevo manifiesto universal v3 y proyección única

Representar toda publicación nueva, incluso inferencia, como un manifiesto v3 universal. Conserva los originales históricos en archivos, pero convierte sus vistas al agregado común para lectura/import. Una única estructura de slots debe representar generación, CPU, upload, Analysis, operaciones de biblioteca y material sin Asset. Es una alternativa real de formato, no una ampliación opcional de v1.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: reconciliar vista común con todas las autoridades y entidades existentes |
| Riesgo | Alto: conversiones semánticas y slots no aplicables; pérdida de significado al proyectar historia |
| Coste relativo | L: migración de consumidores y adaptadores adicionales |
| Reversibilidad | Media: bytes archivados recuperables, pero vistas y consumers nuevos acoplados a v3 |

Las sentinelas, reinterpretar v2 por su número o añadir engine/model/seed a CPU/upload/import no son opciones admisibles. Contradicen ADR-0074 y D-02. No se añade `job/analysis/import/backup` a Asset ni se fabrica Song/Take para operaciones de biblioteca.

## 3. Criterios de decisión

1. Un original publicado conserva sus bytes, ID, versión y semántica. La lectura no añade defaults ni recalcula hashes históricos.
2. Sujeto, origen de ejecución, antecedentes y autoridad permanecen distintos. CPU sobre una fuente de inferencia sigue siendo CPU; post M1 de inferencia mantiene su autoridad v1.
3. Un lector necesita familia, versión y reader admitidos; nunca infiere tipo por campos ausentes, extensión o hash.
4. Todos los sujetos y los 19 pares D-02 tienen destino verificable sin ampliar enums ORM por analogía.
5. El cierre conserva letras históricas, padres/roles/maps, resultados y rights. Import/remap no reescribe originales ni reactiva autoridad.
6. N0 consume audio/timing/features específicos; escena reproducible con tiempo explícito, sin depender del estado web actual.
7. La compatibilidad documental no se presenta como import, backup, inferencia o render ya probados.

## 4. Opción elegida y contrato normativo

**PF-O1, elegida por ROOT bajo delegación explícita el 2026-10-11.** La evidencia de `manifest.py` y `snapshots.py` fija lectores v1 actuales. ADR-0074 obliga a mantener fronteras CPUv2/SongCPUv2. PF-O1 respeta esos hechos y los criterios1–5, mientras TimelineV2 satisface el criterio6. PF-O2 se descarta por introducir proyecciones unificadas de historia que no aportan una autoridad real y complican la separación de sujetos. Revisión/adopción del candidato y ADR específico siguen pendientes.

### 4.1 Tipos, bytes y dispatch

Tipos nuevos heredan D-02: ULID, SHA256 hexadecimal minúsculo, Revision1..9223372036854775807, UInt estricto, UTC, segundos finitos. Bool no es int. Objetos cerrados, claves duplicadas rechazadas antes de construir mapas, sin NaN/Infinity/BOM/coerción. Capturas nuevas usan UTF-8, claves ordenadas, `ensure_ascii=false` y separadores`,`/`:`; SHA cubre bytes completos. No se aplica esa serialización a originales existentes: su SHA es sobre **los bytes originales**, incluidos su whitespace y orden. El hash de texto UTF-8 de letra, de medio, de JSON canónico y de archivo histórico son dominios distintos.

`ByteRef` nuevo, exclusivo del transporte/publicación D-04, tiene exactamente `{family,reader,version,path,sha256,bytes}`. family/reader/versión son pareja registrada, path POSIX relativo seguro, bytes UInt y SHA del archivo referido. No incluye su propio digest. No modifica `HistoricRef` ni `CapturedRef` D-02: un adaptador server autorizado envuelve sus referencias sin añadirles campos ni cambiar su dominio. El catálogo D-08 resuelve ByteRef a una entrada única y verifica family/reader/version, bytes y SHA; ninguno acredita permisos. Reader nunca viene del cliente como handler ejecutable.

| Familia / versión | Reader propuesto / registro | Regla de lectura y emisión |
|---|---|---|
| `manifest/1` | `manifest.inference/1` | Reader histórico v1 y schema actuales. Bytes/semántica originales; nuevas inferencias sólo usan v1 si satisfacen realmente su schema/autoridad |
| `manifest/2` CPUv2 | `manifest.cpu/2` | Frontera cerrada ADR-0074 para CPU autónomo y preview propia. Reader/schema final pendiente de su implementación M2; D-04 no amplía esa familia |
| `song/1` | `song.inference/1` | Lector/proyección histórica existente, sin añadir campos CPU ni M3 |
| `song/2` SongCPUv2 | `song.cpu/2` | Cierre CPU/historia mixta según ADR-0074, schema cerrado propio sin extensión D-04 ni defaults v1 |
| `closure/1`, SongBundleM31 | `production.song_bundle/1` | Índice M3 nuevo §4.5 que refiere Songv1/SongCPUv2 originales sin cambiar sus bytes ni schema; proyección/catalog/cierre D-08 |
| `timeline/1` | `timeline.montage/1` | Shots y campos originales; conservar bytes. No se interpreta como N0 |
| `timeline/2` | `production.timeline_n0/2` | Schema N0 cerrado de §4.4, sin alterar timeline1 |
| `publication/1`, ProductionArtifact1 | `production.artifact.asset/1`, `.analysis/1`, `.artwork/1`, `.render/1`, `.export/1`, `.import/1`, `.backup/1` | Siete readers exactos, combinación literal con subject; D-03 CapturedRef family publication. Sin renderer/handler genérico |
| `publication/1`, ProductionPackage1 | `production.package.asset/1`, `.analysis/1`, `.artwork/1`, `.render/1`, `.export/1`, `.import/1`, `.backup/1` | Cierre de unidad antes de publicación, §4.3; CPU preview sigue family phase y gate T14, no paquete committed |
| Familias D-02/D-03 y perfiles | Mapping exacto adoptado D-02/D-03, versión propia | Recipe/request/receipt y11sellos conservan conjuntos/reader/versión de sus fuentes. D-05–09 schemas externos no se inventan aquí |

Para manifiesto histórico el family/version tiene un único reader admitido; si algún formato previo v2 aún no está liberado, se rechaza `PRODUCTION_DEPENDENCY_UNAVAILABLE`, no se intenta v1. Reader/version desconocida: `PRODUCTION_VERSION_UNSUPPORTED`. Cambiar reader sin cambiar versión/familia registrada es conflicto, no negociación. Una versión incompatible necesita ADR específico antes de schema/código. No hay fallback a «último lector», JSON libre o compatibilidad por poder parsear.

Registro literal de los siete sujetos. Artifact y Package usan family publication/version1; prepared usa family phase/version1. Cada celda es un reader distinto con fieldset exacto, no expansión runtime de strings del cliente.

| subject.kind | Artifact reader | Package reader | Prepared reader |
|---|---|---|---|
| asset | production.artifact.asset | production.package.asset | production.prepared_artifact.asset |
| analysis | production.artifact.analysis | production.package.analysis | production.prepared_artifact.analysis |
| artwork | production.artifact.artwork | production.package.artwork | production.prepared_artifact.artwork |
| render | production.artifact.render | production.package.render | production.prepared_artifact.render |
| export | production.artifact.export | production.package.export | production.prepared_artifact.export |
| import | production.artifact.import | production.package.import | production.prepared_artifact.import |
| backup | production.artifact.backup | production.package.backup | production.prepared_artifact.backup |

### 4.2 ProductionArtifact1: campos exactos y siete sujetos

ProductionArtifact1 es un **índice de evidencia**, no una autoridad transmisible. Campos obligatorios comunes exactamente: `{schema_version,subject,created_at,operation,execution,inputs,revisions,outputs,rights_ref,commercial_use,publication_ref,history}`. schema_version literal1. `operation` una pareja D-02 válida; no enum ampliable por registro. `publication_ref` ByteRef de ProductionReceipt1 final propio, privado; para failed/missing Analysis no hay artefacto publicado. History es lista ordenada de ByteRef de originales necesarios, sin convertirlos. No lleva `seal_kind`, `root.kind` o payload arbitrario; esos discriminantes pertenecen únicamente a los11schemas internos D-03. Hash del envelope va en el catálogo/captura, fuera de sí mismo.

`subject` es objeto cerrado discriminado. Las siete variantes tienen `{kind,result_key,entity_ref,scope}`; result_key ULID reservado D-02. scope exactamente `{kind:song,id:ULID}` o `{kind:library,ref:ByteRef}`. entity_ref es `{kind,id}` para entidad persistente, o `{kind:capture,ref:ByteRef}` para operación sin entidad. No owner de destino suministrado como permiso. Import puede transportar identidad **source** reservada, nunca crear una Song ficticia durante validación.

`inputs` tiene objetos exactos `{role,source_ref,rights_ref}`: role Label de pareja/perfil ratificados, source_ref ByteRef; rights_ref ByteRef al sello D-03 correspondiente. `revisions` tiene `{role,ref}` con role enum stems/mix/audio/analysis/timing/preset/video/lyrics_context/metadata/scene/features/profile y ref ByteRef. Cada pareja exige su conjunto exacto; roles opcionales sólo si el perfil capturado los permite y la solicitud los pidió. `outputs` es inventario exacto de medio `{role,path,sha256,bytes,media_type}`; no incluye su propio manifiesto/package ni receipt autorreferente. El vocabulario de roles/media_type pertenece a su reader ratificado, no extensión libre. Analysis/import/backup pueden no tener Asset, pero sus medios/catálogos se inventarían aquí sólo si existen realmente.

`execution` es una de las siguientes variantes cerradas. En todas `receipt_ref` señala ProductionReceipt1 de ejecución existente y `request_ref` ProductionRequest1 privado inerte; ID de ejecución está dentro del receipt y no se copia como autoridad activa. No se mezclan campos entre ramas.

| `kind` | Campos además de kind | Restricción |
|---|---|---|
| `engine` | request_ref, receipt_ref, provenance_ref | Receipt engine_raw real; provenance_ref reader tipado de selección/terminal; modelo/semilla sólo efectivos si la capability los usa. No seed inventada para analyzer determinista |
| `cpu` | request_ref, receipt_ref, plan_ref | cpu_result propio; tools/mediciones están en receipt/plan original, no modelo/ganador heredado |
| `upload` | request_ref, receipt_ref, source_ref | upload_result real; origen copy/validación, sin inferencia |
| `import` | request_ref, receipt_ref, package_ref, identity_map_ref | Receipt import final propio; preserva ejecuciones históricas en history, sin volverlas ejecuciones del importador |
| `maintenance` | request_ref, receipt_ref, action, cut_ref | action enum backup/restore/activate; cut D-09 real, nuevo cómputo sólo declarado si efectivamente existe, nunca engine simulado |

Los nombres `engine/cpu/upload/import/maintenance` son **clases de evidencia D-02**, no cinco nuevos engines ni permisos. No se introduce «hybrid» en execution: el resultado tiene la ejecución real y varios antecedentes explícitos. Si existen etapas engine→CPU genuinas se conserva cada receipt en history y el final referencia su ejecución real; un post M1 conserva su manifiesto v1, no se reclasifica CPUv2 por el dispositivo.

| Sujeto | entity_ref / scope / execution admisible | Body especializado adicional obligatorio | Formato, CPUv2 y cierre |
|---|---|---|---|
| asset | take Asset/set: `{kind:take,id}`/song; engine para stems, cpu para features; preview no usa este artefacto final | `asset_set_ref:ByteRef` reader stems D-03 o features D-07, sin enum libre | Histórico stems v1 intacto. Resultado M3: ProductionArtifact1.asset. CPUv2 sólo si ese resultado ya pertenece a la familia CPU de ADR-0074; si no cabe se usa familia nueva sin modificar v2. Preview privado T14 no portable |
| analysis | `{kind:analysis_result,id}` o `{kind:timing_revision,id}`/song; engine o cpu real | `result_ref:ByteRef` al analysis/timing exacto, `method` enum beats/sections/key/loudness/lyrics_timing | Analysis histórico conserva data/versión y su SHA; no forzar manifest1 ni Asset analysis. Resultado M3: ProductionArtifact1.analysis; CPUv2 de Take no cubre automáticamente Analysis |
| artwork | `{kind:artwork,id}`/song; engine o upload | `artwork_ref:ByteRef`, `artwork_kind` cover/keyframe/background | Image v1 existente intacta. Generación/edición nueva ProductionArtifact1.artwork; upload rama upload, ningún CPUv2 con seed ficticia |
| render | `{kind:render,id}`/song; cpu | `video_ref:ByteRef`, `timeline_ref:ByteRef`, `scene_ref:ByteRef`, `audio_ref:ByteRef`, `timing_ref:ByteRef` | Render v1 histórico intacto. N0 nuevo ProductionArtifact1.render con TimelineV2. CPUv2 Take no se amplía a renderer por analogía |
| export | `{kind:export,id}`/song; cpu | `export_kind` audio/stems/video/lyrics/project_zip, `profile_ref:ByteRef`, `metadata_ref` siempre explícito: NULL literal para project_zip; ByteRef obligatorio para audio/stems/video/lyrics | Export nuevo ProductionArtifact1.export. Audio original conserva bytes aun con envelope propio CPU; no reemite manifest padre como si export fuera inferencia |
| import | `{kind:capture,ref}`/song source reservada; import | `package_ref:ByteRef`, `catalog_ref:ByteRef`, `closure_ref:ByteRef`, `identity_map_ref:ByteRef` | ProductionArtifact1.import privado; no Asset import ni Take. Originales v1/v2 y envelopes nuevos se conservan; no CPUv2 como inferencia del importador |
| backup | `{kind:capture,ref}`/library; maintenance | `action` backup/restore/activate, `package_ref:ByteRef`, `catalog_ref:ByteRef`, `cut_ref:ByteRef`, `validation_ref:ByteRef`; activate además `rollback_ref:ByteRef` | ProductionArtifact1.backup privado, LibraryPackage D-09. No SongCPUv2 ficticia para biblioteca; conserva snapshots de cada Song y medios del mismo corte |

Las cinco parejas export de D-02 ligan operation, export_kind, parameters.kind y perfil capturado exactamente. Esta tabla no inventa un perfil ni amplía su reader.

| operation / subject | export_kind = parameters.kind | Payload y perfil real D-02 | metadata_ref obligatorio |
|---|---|---|---|
| export_audio / export | audio | `{kind:audio,target:original\|streaming\|broadcast\|podcast}`; audio/mix y audio_export, D-05 | ByteRef `production.export_metadata/1` |
| export_stems / export | stems | `{kind:stems}`; set stems cerrado y stems_export, D-05 | ByteRef `production.export_metadata/1` |
| export_video / export | video | `{kind:video,render_id}`; Render committed autorizado y perfil render/export ratificado, D-07 | ByteRef `production.export_metadata/1` |
| export_lyrics / export | lyrics | `{kind:lyrics,format:lrc\|srt,timing_revision_id}`; letra histórica/bindings y RevisionRef timing, D-06; profile_ref sólo al perfil cerrado ratificado para esta pareja | ByteRef `production.export_metadata/1` |
| export_project / export | project_zip | `{kind:project_zip}`; cierre/root históricos y portable, D-08 | NULL literal, incluso si Song tiene Takes |

El campo metadata_ref nunca se omite. Project no admite ByteRef de metadata de Take; los cuatro exports de medios no admiten NULL ni fallback. Operation/kind/payload/profile cruzados o no ratificados son INVALID. Un gate o reader pendiente causa DEPENDENCY_UNAVAILABLE antes de efectos; ningún perfil inventado produce output.

En esta tabla los campos body están en el root del reader de ese sujeto **además** de los comunes. No objeto `body` libre. Un campo de otra fila es extra y rechaza. Resultante asset_set_ref sólo acepta reader `production.stem_set/1` o `production.features/1` ratificado D-07 según operation; no «cualquier asset». Method/result_ref deben coincidir con la operación y el sello SQL; timing correct conserva initial/audio/context. Artwork_ref, scene_ref y metadata_ref no NULL necesitan reader cerrado identificado más abajo o en gates propios. SourceRef Analysis representa bytes JSON, no audio inexistente.

`production.artwork/1` (family revision) es captura privada nueva exactamente `{schema_version,id,owner_id,created_at,updated_at,deleted_at,song_id,kind,source,upload_id,job_id,prompt_ref,model_id,seed,rights,source_refs,asset_refs,rights_ref}`. schema_version1; campos Common/Artwork conservan sus tipos actuales: IDs ULID, UTC, deleted_at NULL o UTC, song_id ULID M3, kind cover/keyframe/background, source generated/upload, rights own/licensed/consented/public_domain. prompt_ref es ByteRef al texto privado capturado o NULL, nunca prompt inline en manifiesto. Upload exige upload_id real, job_id/model_id/seed/prompt_ref NULL y source_refs incluye ese upload; generated exige job real, model_id efectivo Label y seed real sólo si ese modelo/capability la usa, nunca inventada para llenar schema; referencia a selección engine y stage reales por el receipt. Valores nullable se representan explícitamente. source_refs/asset_refs son listas de ByteRef exactas para fuentes de edición y assets del Artwork, ≤64, sin extras. Rights_ref conserva sello D-03; los derechos del campo rights no sustituyen ese cierre. Este reader conserva datos Artwork originales en captura separada sin cambiar el ORM ni su proyección histórica. D-11 ratifica workflow/capability/schema generado, no queda JSON libre. `production.export_metadata/1` (family revision) se fija en §4.6. `production.scene_n0/1` (family revision) se fija en §4.4. El mismo cierre de family/reader/version rige estas refs; no se ejecuta sin esos schemas adoptados.

### 4.3 ProductionPackage1, paths y límites

Package de publicación D-04 es captura privada exactamente `{schema_version,subject,request_ref,preparation_evidence_ref,artifact_ref,required_roles,members}`. schema_version1; subject mismo objeto del artefacto; preparation_evidence_ref señala evidencia **existente anterior al commit**, nunca receipt final anticipado. Asset/Analysis/Artwork/Render/Export requieren receipt de engine/cpu/upload real con su reader D-02; Import requiere validación de cierre y mapa reader `production.import_validation/1` D-08; Backup requiere `production.maintenance_execution/1` D-09 según acción, conforme a executed sin receipt final de D-03. No receipt import/maintenance succeeded antes committed. artifact_ref es ByteRef del envelope **prepared**, sin publication_ref. El package no incluye el final artifact ni los bytes/hash del final receipt. D-03 reserva identidad del receipt por su fase/intención y lo materializa en commit después de verificar package; sólo entonces el artifact final lo referencia. Captura prepared y final son objetos diferentes con hashes propios, no dos fases de un archivo mutable.

Concreción sin hash circular: artifact_ref en Package apunta a `production.prepared_artifact.<subject>/1` (family phase). En Asset/Analysis/Artwork/Render/Export sus campos son exactamente el artefacto final menos publication_ref. Export preparado conserva §4.2: project_zip exige metadata_ref NULL explícito; audio/stems/video/lyrics exigen ByteRef. Package conserva esa misma regla mediante artifact_ref, sin optional/fallback. En Import/Backup, execution se reemplaza por el objeto cerrado `preparation={kind:import|maintenance,request_ref,evidence_ref}`, con evidencia previa indicada arriba. Se omiten los campos que requieren receipt final: execution, identity_map_ref de execution y cut_ref de execution. Los campos especializados de root conservan referencias a capturas previas reales de validation/map/cut/package. Este reemplazo define **dos schemas distintos**, no un optional/fallback genérico. Final receipt package_ref hashea este package preparado. Después del commit se emite ProductionArtifact1 final con execution real final y publication_ref hacia ese receipt. Package→prepared artifact→evidencia previa es DAG; final artifact→final receipt→package también es DAG. El final artifact no se incluye como member del package que el receipt hashea. Readers prepared sólo validan preparación; nunca autorizan serving. No insertar campo reservado D-03 en estos envelopes.

Members exactamente `{role,ref}` y conjunto igual al requerido más las dependencias privadas tipadas que el cierre enumera. required_roles lista única ordenada; no «todo lo que había en carpeta». Los miembros de medios se comparan con outputs, paths, hashes y tamaños y los conjuntos tienen igualdad, no subset. Un fallo de un rol bloquea toda la unidad, conservando unidades independientes válidas D-02. Preview temporal continúa `production.temporary` family phase, gate T14; no committed ni paquete portable final.

Layouts nuevos propuestos, relativos a raíz del paquete, no a un volumen personal: `content/<sha256>` para bytes medios, `evidence/<family>/<reader>/<version>/<sha256>.json` para capturas públicas admisibles, `private/<family>/<reader>/<version>/<sha256>.json` para payload privado autorizado; nombres de family/reader son tokens ASCII del registro server, no strings interpolados del cliente. Se preserva nombre/path histórico en catálogo original, y la ruta física nueva en catálogo/mapa separados. No se cambia `output.path` de un manifiesto histórico para apuntarlo al layout: reader histórico usa una vista relativa confinada del layout original o resolver de catálogo explícito, ambos con bytes idénticos. Si no es posible resolver sin sobrescribir/alias, se rechaza.

Paths ≤1024 caracteres, POSIX, relativos, no vacíos, sin `.`/`..`/segmento vacío, backslash, drive, UNC, colon, controles, nombres Windows reservados, trailing punto/espacio, symlink/junction/hardlink/archivo especial. Se rechazan entradas duplicadas y alias por normalización Unicode/case en el destino, incluyendo archivo/directorio mismo path y escapes de nombres ZIP. No seguir links ni convertir separators para tolerar un archivo inválido. La confinado se revalida durante cada copia; validar nombres una vez no evita carrera con FS.

| Límite D-04 nuevo | Valor / frontera |
|---|---|
| ProductionArtifact1 y prepared artifact | Cada JSON canónico ≤1048576 bytes, profundidad≤32, strings Label≤512 salvo path≤1024 |
| ProductionPackage1 | JSON canónico≤2097152 bytes, profundidad≤32 |
| inputs / revisions / outputs / history | Cada lista≤64 por unidad; identity/role duplicados prohibidos cuando el reader exige unicidad |
| required_roles / members | Roles≤64; members≤256 de unidad de publicación, sin convertir un cierre Song grande en unidad inline |
| TimelineV2 y SceneN01 | Cada JSON canónico≤1048576 bytes, profundidad≤32, ≤64 refs de artwork/features/fonts y ≤64 capas de escena |
| Paquete Song/biblioteca, catálogo, media, duración, cuotas descomprimidas | **D-08/D-09**, no se extrapolan límites del request ni del envelope. Gate ausente bloquea antes ingest/export; sin truncar historia o canción |

D-04 fija topes de índices **nuevos**, no impone esos límites a bytes históricos. Un original grande se transporta por ByteRef y cuota D-08, no se reserializa ni fragmenta implícitamente. Los 64 outputs no limitan archivos de un proyecto ZIP; su cierre vive fuera del envelope mediante catalog/closure refs D-08.

### 4.4 TimelineV2 y SceneN01

TimelineV2 tiene exactamente `{version,video_project_id,revision,duration_s,fps,audio_ref,timing_ref,scene_ref,lyrics_context_ref}`. version literal2; ULID/revision real VideoRevision D-03; duration_s igual al binding audio final medido, fps racional positivo reducido; audio_ref reader production.audio_binding1, timing_ref reader production.lyrics_timing_revision1, lyrics_context_ref production.lyrics_context1, scene_ref production.scene_n01. Referencias deben coincidir con m3_video_revision, no otro master/preset/current_lyrics. Hash externo al objeto. No hay texto privado en TimelineV2. El texto para captions viene de las versiones históricas privadas ligadas a timing/context; cambiar current_lyrics_version_id no altera el render.

SceneN01, reader `production.scene_n0/1`, family revision, campos exactos `{schema_version,canvas,background,visualizer,captions,fonts,profile_ref}`. schema_version1. canvas exactamente `{width,height}` ints1..16384; dimensiones efectivas del perfil D-07, no autorización para un render de cualquier tamaño. Profile reader D-07 fijo; límite1MiB no acredita rendimiento. No JS/CSS libre, URL, código, paths de sistema o browser executable.

| Objeto | Campos / enums cerrados |
|---|---|
| background | Una de `{kind:color,rgba:[float,float,float,float]}` con canales0..1, o `{kind:artwork,artwork_ref:ByteRef,fit:contain|cover,rgba:[4float]}`; artwork source autorizado. No imagen de red |
| visualizer | `{kind:none}` o `{kind:waveform|spectrum|particles,features_ref:ByteRef,profile_ref:ByteRef,visual_seed:UInt}`. Para none no features/seed inventados. Visual_seed ≤2^64−1, es semilla visual **CPU**, no semilla de inferencia. Features y perfil D-07 contienen parámetros cerrados, ratificados aparte |
| captions | `{kind:karaoke,timing_ref:ByteRef,lyrics_context_ref:ByteRef,font_ref:ByteRef,profile_ref:ByteRef}`. N0 de karaoke exige esa rama; perfil closed D-07 conserva posición/tamaño/colores/márgenes/wrapping/highlight/incertidumbre. No texto duplicado ni fallback letra actual |
| fonts | Lista ordenada de ByteRef locales cuyo reader/pin/licencia se ratifica D-07; cubre exactamente fonts consumidas por captions/profile, no URL ni descarga al render |

Color y artwork tienen fieldsets disjuntos; un particles sin features/seed/profile rechaza. Timing word token pertenece a letra/binding conservados, t0/t1 dentro duración y confidence/missing/uncertain del sello D-03. Missing no se convierte en palabra cantada, instrumental no activa palabras y composite no se reasocia por longitud. Captions conserva incertidumbre visible según perfil ratificado; no se impone un valor optimista por defaults.

Contrato temporal N0: `scene(time_s)` es función reproducible con assets/fonts/seed/features fijados. Preview usa reloj del audio; export cuadro k usa tiempo exacto `k*fps_den/fps_num`; 0≤time<duration. Frame count `ceil(duration*fps_num/fps_den)` y último cuadro no añade audio ficticio. Seek recompone estado absoluto, no depende de frames previos ni requestAnimationFrame. Features representan audio efectivo con ventana/hop/offsets y política de bordes/silencio D-07; cambio de mix/audio exige nuevas features. No usar espectro del padre para un mix nuevo. browser/font/codec/mediciones e igualdad preview/export se prueban en D-07/T correspondientes; estas fórmulas no acreditan tiempo real ni calidad visual.

RenderPlan derivado no es segunda autoridad: referencia VideoRevision+TimelineV2/SceneN01/audio/timing/features/artwork/perfil exactos y conserva sus SHA. Una revisión nueva del proyecto no cambia un plan capturado. Timeline1 sigue su lector montaje; convertirlo a N0 requiere acción explícita que crea revisión nueva con referencias originales, no overwrite ni conversión silenciosa.

### 4.5 SongCPUv2 y cierre completo multiversión

Songv1 histórico permanece exacto. Si la historia no incluye CPU, su proyección v1 se conserva; si el cierre incluye CPU autónomo se requiere SongCPUv2 con reader exacto `song.cpu/2` según ADR-0074. D-04 **elige siempre familia nueva SongBundleM31 para el índice de export portable M3**; puede referir Songv1 o SongCPUv2 y nunca altera esos schemas. Tener sólo derivados M3 sin Take CPU no cambia por sí mismo el origen musical ni el número del snapshot histórico. El bundle completa las nuevas revisiones de producción por refs/proyección D-08, sin insertarlas como campos nuevos de Songv1/SongCPUv2.

SongBundleM31, reader `production.song_bundle/1`, family closure, fija exactamente `{schema_version,song_id,snapshot_ref,originals,projection_ref,closure_ref,catalog_ref,history_refs}`. schema_version1; song_id original; snapshot_ref refiere Songv1 o SongCPUv2 según cierre CPU y corresponde a song_id. Originals es lista ByteRef de snapshots/manifiestos/planes históricos que efectivamente existen; projection_ref reader cerrado `production.song_projection/1` (family closure D-08), closure/catalog refs D-08. History_refs conservan capturas inertes de requests/receipts/revisiones necesarias. No fields live ni row/payload libre. El índice se genera nuevo y es inmutable; sus arrays de referencias admiten cada una≤4096, bytes canónicos≤2097152, profundidad≤32; originales/cierre grandes se refieren por catálogo externo D-08 en lugar de truncar. Si supera estos topes, LIMIT_EXCEEDED antes efectos; no se aplica el límite64 de una unidad al cierre entero.

Así D-04 no declara otra representación bajo `song/2` ni deja alternativa de formato para elegir en runtime. El schema cerrado CPUv2 final M2 y su lector deben existir y estar liberados para producir/leer snapshot_ref CPU; en este corte no están y esa operación falla cerrada hasta su tarea correspondiente. Bundle no inventa un SongCPUv2 con bytes o filas ficticias para eludir esa dependencia. Esta comprobación precede al primer RED dependiente. ManifestCPUv2 conserva la misma regla: no añadir sujetos M3 al enum previo; ProductionArtifact1 los expresa sin cambiarlo.

La proyección de filas locales nueva, reader `production.song_projection/1`, no es «rows libres». Sus schemas admiten exactamente las proyecciones de entidades originales adoptadas y las familias D-03 enumeradas, con campos, XOR, NULLs, FK, pertenencia y guards correspondientes. El inventario D-08 fija tablas/columnas transportables y cómo convertir campos operativos en historia inerte. D-04 fija el **cierre requerido**, no inventa columnas SQL ni adopta un schema pendiente mediante un hash.

| Parte del cierre obligatorio | Qué conservar y comprobar |
|---|---|
| Song / master / metadata | ID/procedencia original, título/artista/año y demás valores históricos, revisiones, valoraciones/favoritos/tags/notas pertinentes; maestro elegido y cover seleccionado, sin cambiar selección automáticamente |
| Takes y padres | Todas las tomas de la canción, incluidas historia eliminada lógicamente cuando pertenece al contrato de export; ancestros transitivos requeridos, derivation/root original, todos los padres ordenados/roles y maps efectivos por arista; DAG/raíz/pertenencia según ADR-0041 |
| Audio/Assets | Todos los medios declarados y necesarios: master/previews persistentes permitidas/stems/features/artwork/render/export; original bytes, roles, hash, size, sample rate/channels/frames/duration medidos y offsets comunes. Preview temporal privada T14 queda excluida explícitamente y no se vende como parte persistente perdida |
| Letra/referencias | Versiones completas históricas, own/assistant/declaraciones, single/composite, fragmentos y rangos originales, bindings/hash, tokens y TimingRevision initial/parents/correcciones; no sólo current_lyrics |
| Analysis/Mix | Resultados por método y outcome, evidencia legacy original inmutable, pins, audio binding medido; StemSet y4controles MixRevision, padre/revisión/perfil y combinación real, sin resultado missing convertido success |
| Imagen/personajes/uploads | Artwork original/generated/upload, antecedente, imagen/foto necesaria en payload privado autorizado; fuentes/ref/character_ref/declaraciones/consent y lineage aplicable, ningún path personal |
| Vídeo | VideoProject/revisiones, Timeline1 original o TimelineV2/SceneN01, shots/versions cuando existan, artwork/audio/timing/features/fonts/licencias y Render; nunca sólo MP4 final |
| Exportaciones | Receta/perfil y reader versionado; audio/stems/video/lyrics conservan metadata de Take, portada/letra histórica solicitada y bytes/manifiesto. Project_zip conserva metadata_ref NULL y metadatos/letra/portada/revisiones de Song por closure, incluso master NULL/takes []; no fabrica Take/audio. Historial original separado de ejecución de import |
| Presets / referencias globales | Revisiones efectivas consumidas, valores capturados y fuentes/timbre declaradas, no sólo alias mutable global; colección/personaje externo necesarios como dependency-only sin mezclar propietarios |
| Procedencia/rights | Requests/recipes/receipts/planes/manifiestos originales por family/version/reader, declaraciones y SHA; tools/model/pins/licencias que realmente participaron y commercial_use conjuntivo. No pesos incluidos por defecto ni hash=permiso legal |
| Custodia/historia operativa | Hechos históricos inertes necesarios para causalidad; excluir tokens/secretos/leases/PIDs/custodia activa/worker bindings. Original admisible conservado; no reactivar job queued/running por copiar status histórico |

Se calcula cierre hasta punto fijo de refs tipadas y ancestros, más **toda historia de contenido de la Song**, no sólo antecedentes del master. El catálogo registra cada objeto una vez por identidad source/family/version/hash y cada relación explícita. Una referencia externa obliga incluir dependencia mínima completa con propietario original y permiso de lectura/export vigente; si falta, export falla sin paquete aparentemente completo. Puede haber ref cíclica de entidades Song/master, pero causalidad Take/revisiones tiene DAG; el lector valida ambos ámbitos separadamente. Se conserva contenido necesario para historia, no secretos de terceros.

Material privado autorizado viaja en `private/`, fuera de manifiestos y logs; el paquete entero se considera privado. ByteRef es sólo ubicación relativa/hash, no letra/prompt/foto. Manifiesto v1 original que incluya contenido prohibido, rutas absolutas o secretos **no es portable admisible**: export falla sin reescribirlo. No se entrega paquete «sanitizado completo» que pierde original. Un formato de redacción autorizado distinto necesitaría decisión de producto/ADR y declaración de pérdida, fuera de esta elección.

Backup de biblioteca incluye SQLite/catálogo/media/refs del mismo corte y schemas/locks aplicables; Song bundles no sustituyen un backup consistente. D-09 establece cut, restore nuevo y activación raíz/BD conjunta, jobs históricos inertes, integridad/FK/FTS/reproducción y rollback. No copia VHDX activo como backup; no archive runtime credentials. D-04 declara cómo leer history, no suspende workers ni acredita plataforma física.

Song válida sin tomas conserva master NULL y takes [], título, letras históricas, portada y revisiones de Song mediante el cierre. Export project no exige metadata de Take ni fabrica Take/audio; ejecutar el paquete por CPU no convierte su snapshot Songv1 en SongCPUv2. SongCPUv2 y SongBundleM31 conservan la misma regla de cierre para una Song sin tomas admisible por sus lectores, sin redefinir schemas históricos.

### 4.6 Original, stems y metadatos/letra

Audio `target=original`: bytes exactos del asset seleccionado y mismo SHA; no transcodifica, remuestrea, normaliza ni embebe tags si eso cambia esos bytes. Metadata/cover/lyrics solicitados se entregan en sidecar versionado propio cuando se pide original. Si el usuario solicita obligatoriamente **embebido** junto con original byte-exacto, la combinación es incompatible y se rechaza antes ejecutar; UI debe explicar/elegir export derivada o sidecar, no incumplir una de las dos promesas. Los demás targets conservan perfiles D-05, ganancia constante/soxr y comprobación final decodificada; no limitador silencioso.

StemsZIP contiene exactamente `stem:vocals`, `stem:drums`, `stem:bass`, `stem:other` y metadata/manifiesto/catálogo definidos por perfil D-05; engine_role y Asset.role permanecen namespaces distintos. WAV/FLAC48kHz del perfil conserva origen temporal0, frame count común, canales/perfil, duración, amplitud y alineación. Sin normalización por pista ni ganancia implícita. Cada pista declarada tiene bytes/hash y medición reales. ZIP completo sólo se publica después de verificar los4roles; t0/offset/sr/frames no se inferieren del nombre. La conversión/resampler efectivos se declara y valida por métricas D-05, no se promete igualdad de bytes después de convertir.

Reader nuevo `production.export_metadata/1` family revision, exclusivo de audio/stems/video/lyrics y sin ampliar su fieldset: exactamente `{schema_version,title,artist,year,take_id,audio_ref,artwork_ref,lyrics}`. schema_version1; title/artista son strings capturados privados1..512 o NULL explícito sólo si no suministrados; year int1..9999 o NULL; take_id ULID del take efectivo, no el master actual; audio_ref exacto, artwork_ref ByteRef o NULL según solicitud. lyrics es `{mode:omit}` o `{mode:embedded|sidecar,context_ref:ByteRef,timing_ref:ByteRef|null}`. Omit no copia texto/hash de letra ni emite tag lyrics. El `context_ref` refiere texto histórico single/composite y bindings, never current_lyrics; timing_ref sólo cuando export LRC/SRT o tipo sincronizado lo necesita. Campos de texto privado no se ponen en ProductionArtifact ni logs.

El lector independiente del proyecto portable recupera título, letras históricas, portada y revisiones de Song por Songv1/SongCPUv2/SongBundleM31 y closure. Admite master NULL/takes [] sin metadata de Take/audio ficticios; project_zip mantiene metadata_ref NULL literal incluso si tiene Takes. El reader metadata de medios no se usa para el proyecto. El lector independiente del contenedor resultante de audio/stems/video/lyrics debe recuperar título/artista/año/take_id/portada y texto histórico solicitado; los nombres reales de tags/content types/formato cover dependen del codec/perfil D-05/D-07 y deben concretarse antes RED de export. No se declaran soportados MP3/MP4/FLAC/WAV en este candidato por extensión. LRC/SRT consumen revisión explicitada, offsets/orden/rounding/perfil D-06 y conservan missing/uncertidumbre sin palabras fabricadas. Generar sidecar/metadata es cómputo CPU real con Export propio; importar/copy video no se declara nuevo render.

### 4.7 Dedupe, IDs y remapeo sin overwrite

Identidad original es tupla `(source_library,entity_kind,source_id)` acompañada de hash/captura y owner original. Source_library es identificador portable opaco D-08, no path de máquina ni permiso. El destino revalida autenticación/owner y asigna IDs propios donde corresponde. Source→local es mapa separado versionado `production.identity_map/1` D-08, no reescritura del manifiesto, Song original, IDs/owner en evidencia. Toda proyección remapeada tiene ID/hash nuevos y vínculo al original; maestro/padres/roles/maps/letras refs/media/artwork/render/export se resuelven **todas** mediante el mismo mapa, no reemplazo textual de strings en JSON.

| Situación | Política seleccionada |
|---|---|
| Replay misma intención/request y paquete/source hash | Sólo con receipt import committed **propio**, mismo closure/map/binding/resultado. Devuelve terminal exacto; no reimporta, no genera inferencia |
| Mismo ID y mismo hash sin receipt propio | No adoptar por hash. Conflicto hasta reconciliación autorizada D-08; igualdad de contenido no demuestra pertenencia |
| Mismo ID con otra identidad/bytes/owner | `PRODUCTION_IDENTITY_CONFLICT`/`PRODUCTION_COLLISION` antes promoción; no overwrite ni mezclar usuarios |
| Mismo contenido en identities originales distintas | Puede compartir bytes por content-addressing **sólo** tras autorización y custodia por cada identidad/ref; conserva ambas historias/rights. No dedup semántico global de Takes o owners |
| Remap explícito | Nueva importación/request/result/map; reserva IDs nuevos no-clobber y registra mapping completo de todas las entidades/aristas/refs/paths. Preserva originales exactos, declara dueño local autorizado distinto de dueño histórico |
| Imports concurrentes o ID/path reservado por otro | Reservas propias y CAS por unidad/lote D-08; perdedor no cambia ganador. Contenido promovido propio sin commit queda inerte para reconciliación, nunca serving parcial |
| Conflicto de paths con mismo hash | No-clobber; no reemplazar archivo preexistente ni reclamarlo por digest. Resolver sólo con evidence propia de ese import y binding actual |

El paquete portable incluye mapa identity original o el mapa de import anterior cuando forma parte de historia; el mapa **nuevo de destino** se produce como hecho de import propio fuera de los originales. No se transforma CPU import en inferencia ni añade ejecutor/seed a historia. Hash del paquete acredita bytes; receipt/evidence import de otra biblioteca son historia inerte, no permiso en la actual. D-08 debe fijar schema/quota/algoritmo de map, resolvers y atomicidad lógica antes implementación. Esta elección no habilita remap mientras ese gate falte.

### 4.8 Goldens y negativos por origen y sujeto

**Evidencia disponible:** el golden M1 manifest-v1 del índice tiene1351bytes y SHA f86b3fd6…f97; Songv1 tiene1491bytes y SHA65b3a58d…8fa; PostPlanv1 tiene2154bytes y SHA `d15eb15db03be986d34a4e6b71a8412f1526f8a07ac4825aa01fcbadfc431b76`. Recipe trim sintética CPU cerrada tiene2098bytes/SHA `a9a920d1b509abc6d8f2d85b55e353bf3278a75ef441c9b21ae9a0b3a3110b66`; crossfade sintética3399bytes/SHA `9f5d86eb0e563635e88e0c4641ce6cbdeed0ed1410de22d2e9701a2b7770e6e8`. Se comprobaron hashes contra receipt/índice; no se ejecutó post ni inferencia. No hay bytes v2/SceneN0/paquete portable reales en el corte. Los ejemplos siguientes son **vectores golden normativos para futuras fixtures**, no resultados/media inventados ni validadores probados.

Cada vector fija rama, readers y conservación. «H» es origen histórico de una inferencia real cuando exista; «C» es trabajo propio CPU/upload/import/maintenance sin inferencia; «X» es cierre híbrido de antecedentes, nunca un executor nuevo. Las letras H/C/X son nombres de caso, no valores JSON admitidos. Una futura fixture completa materializa todos los campos de §4.2–4.7 con capturas sintéticas claras y medios fixture, verifica SHA/bytes externos y prueba negativos. No se pueden usar hashes/IDs sintéticos aquí como permiso de runtime.

| Golden | Sujeto / origen | Ejemplo concreto y expectativa de reader | Negativo requerido |
|---|---|---|---|
| PF-G01-H | asset / histórico inferencia | Set stems v1 existente→manifest.inference1 original+4stem roles/hash; no rewrite a v2 | Sólo3roles o retag engine_role=asset_role sin descriptor: PACKAGE_INVALID |
| PF-G01-C | asset / CPU | Features de audio final→production.artifact.asset1 execution.cpu y audio binding D-03, perfil/features D-07; sin modelo/seed | Features de audio padre con hash distinto al mix: SOURCE_MISMATCH |
| PF-G01-X | asset / híbrido | Features CPU de mix con padres inferencia+CPU→artifact.asset1; history refs v1/v2 y4stems/mix, executor cpu | Copiar engine/seed de padre al execution CPU: INVALID |
| PF-G02-H | analysis / histórico inferencia | Resultado original de alignment/analyzer→data histórica preservada+reader histórico registrado; sin Asset analysis fabricado | Modificar Analysis.data/UNIQUE o analyzer ficticio para insertar: INVALID |
| PF-G02-C | analysis / CPU | Timing correction hija→artifact.analysis1 method lyrics_timing, execution.cpu, mismo initial/audio/context/tokens y tiempos revisados | Cambiar current_lyrics o confidence missing para declarar cantada: SOURCE_MISMATCH/INVALID |
| PF-G02-X | analysis / híbrido | Initial alignment engine auténtico seguido correction CPU→ambos receipts/history, final cpu y bindings composite preservados | Receipt engine_raw usado como publication final o binding reasociado por tamaño: INVALID |
| PF-G03-H | artwork / histórico inferencia | Image v1 realmente existente→bytes v1/hashes/pins/semilla efectivos conservados, no seed de Take atribuida a imagen | Substituir workflow/modelo histórico por preset actual: SOURCE_MISMATCH |
| PF-G03-C | artwork / upload | Attach Upload autorizado→artifact.artwork1 execution.upload, derechos/consent, bytes copia | Falta consentimiento foto real o añadir modelo/seed/generación: RIGHTS_REQUIRED/INVALID |
| PF-G03-X | artwork / híbrido | Edit image engine real desde upload+generated refs→artifact.artwork1 execution.engine y fuentes/rights ambos; Song cover permanece selección aparte | Autoelegir portada, ocultar upload o heredar seed sin ejecución: INVALID |
| PF-G04-H | render / histórico inferencia | Render/manifiestos v1 con clips engine anteriores→timeline.montage1 original, no N0 reinterpretado | Leer timeline1 con reader N0: VERSION_UNSUPPORTED |
| PF-G04-C | render / CPU | N0→artifact.render1 cpu, timeline2+scene1/audio/timing/fonts/features exactos, frame time explícito | Render features de otro master o descargar font de URL: SOURCE_MISMATCH/INVALID |
| PF-G04-X | render / híbrido | N0 CPU consume artwork engine+audio CPU con ancestors inference→history íntegra, executor CPU; captions single/composite histórico | Declarar Render engine porque cover fue engine o truncar canción a180s: INVALID |
| PF-G05-H | export / histórico inferencia | Export v1 histórico permanece lector v1 cuando efectivamente exista y sea admisible | Regenerar manifesto antiguo o semilla para que encaje nueva export: INVALID |
| PF-G05-C | export / CPU | Original bytes exactos +metadata sidecar, o ZIP4stems48k alineados→artifact.export1 CPU y perfiles efectivos | Original byte-exacto con tags embebidos impuestos, normalizar stems o ZIP incompleto: INVALID/PACKAGE_INVALID |
| PF-G05-X | export / híbrido | operation export_project, parameters.kind=export_kind=project_zip, perfil portable; artifact.export1 cpu, metadata_ref NULL en prepared/final y Package, cierre original v1 inference+CPUv2+timing/image/N0 y closure/catalog multiversión | Metadata ByteRef o sólo master/current_lyrics/antecedentes descartados: INVALID/PACKAGE_INVALID |
| PF-G05-P0 | export / Song sin Take | Song válida master NULL/takes [], título/letra histórica/artwork/revisiones; export_project/project_zip y portable, prepared/final CPU metadata_ref NULL y Package igual; snapshot Songv1 y originales/closure conservados, no SongCPUv2 por ejecutar export CPU | Inventar Take/audio o rechazar únicamente por ausencia de Take: INVALID; pérdida de historia: PACKAGE_INVALID |
| PF-G06-H | import / histórico inferencia | Import paquete inference-only→artifact.import1 execution.import, Songv1/manifests1 originales, nuevo receipt/map propio | Atribuir JobAttempt/seed del original al importador: INVALID |
| PF-G06-C | import / CPU | Import SongCPUv2 con Take cpu→reader2 exacto, artifact.import1 import, owners/maps separados y CPU fields NULL originales | Reader v1 tolera null/default0; ocupar ID sin receipt propio: VERSION_UNSUPPORTED/COLLISION |
| PF-G06-X | import / híbrido | Import cierre mixto en destino nuevo→v1/v2/Artifact1/Timeline2, refs fully mapped en proyección nueva, originals iguales | Remap actualiza JSON original, parcial ready o activa leases/PIDs: INVALID/PACKAGE_INVALID |
| PF-G07-H | backup / histórico inferencia | Library backup con Songs inference-only→artifact.backup1 maintenance, cut/SQLite/media mismo corte y snapshots1 conservados | Sólo SQLite, copiar VHDX activo o reactivar job histórico: INVALID |
| PF-G07-C | backup / CPU | Library backup/restore con CPUv2→maintenance propia sin Song ficticia, reader CPU2 e historia inerte | Backup inventa engine; falta media del cut o binding nuevo: INVALID/PACKAGE_INVALID |
| PF-G07-X | backup / híbrido | Restore library completa mixta→schemas/locks/catálogo/bytes/refs, binding+rollback D-09 en activación | Mezclar BD nueva con raíz vieja o activar antes validar FK/FTS/media: PACKAGE_INVALID |

Coverage documental actual: 22 vectores; siete sujetos por tres clases de origen más PF-G05-P0, cada uno con reader/representación y negativo. El conteo anterior ejecutado de 21 queda como evidencia histórica en §7. Cuando no existe v1 histórico real para una rama, el caso H conserva su **evidencia original** con reader registrado; no fabrica un manifiesto v1 que nunca se emitió. Los casos engine M3 nuevos usan Artifact1, si v1 no puede representarlos honestamente. Los casos C de upload/import/backup distinguen su clase sin llamarlos inferencia CPU.

### 4.9 Fallos, criterios y límites de aceptación

| Caso documental | Rechazo / efecto y gate futuro |
|---|---|
| PF-N01 family/reader/version desconocida, bool1, extra, duplicate JSON, BOM, NaN, hash sin dominio correcto | INVALID/VERSION_UNSUPPORTED antes efectos; preservar bytes originales. Parametrizar todas familias/sujetos |
| PF-N02 envelope/package/scene/timeline o lista excede límite exacto y límite+1 | LIMIT_EXCEEDED, sin truncar ni dividir closure implícitamente; probar límites Unicode/bytes/profundidad |
| PF-N03 path absolute/UNC/traversal/alias/case/link/duplicadoZIP/race | PACKAGE_INVALID, staging propio sin promover ajeno; quotas D-08 antes descompresión |
| PF-N04 falta parent/role/map/history/lyrics binding/media/hash/rights/consent | PACKAGE_INVALID/SOURCE_MISMATCH/RIGHTS_REQUIRED; ningún paquete marcado completo |
| PF-N05 commercial_use true con entrada/tool/model realmente usado false o falta declaración | RIGHTS_REQUIRED/INVALID; AND de todas fuentes/padres/letras/tools/modelos efectivos. No AND vacío=true para CPU; faltar tools/rights bloquea |
| PF-N06 import repetido/concurrente/ID ocupado/same hash sin receipt | CAS_CONFLICT/COLLISION; preserve winner y originals, replay propio exactamente, no content=authority |
| PF-N07 raw success usado como commit, custodia UNKNOWN, cancel antes commit | DEPENDENCY_UNAVAILABLE/CUSTODY_UNKNOWN/CANCELLED; no servir/promover/limpiar/liberar. Cancel tardío no revoca committed propio |
| PF-N08 original+embedding incompatible, LUFS/peak imposible, stems partial o desalineados | INVALID/NOT_CONFORMANT/PACKAGE_INVALID; no normalization/limiter silencioso |
| PF-N09 timeline/audio/timing/features/fonts/codec diferente, duración truncada, palabra missing inventada | SOURCE_MISMATCH/DEPENDENCY_UNAVAILABLE/INVALID; gate D-06/D-07, canción completa |
| PF-N10 backup sin exclusividad/cut/medios, restore sin lector/schema, activate sin rollback | DEPENDENCY_UNAVAILABLE/PACKAGE_INVALID; no activar biblioteca parcial ni autoridad histórica |
| PF-N11 byte original contiene secreto/path absoluto/live authority | Export no admisible, sanitizado de error sin payload; no reescribir original para vender cierre completo |
| PF-N12 code-first schema/DTO M1 cambia required/types o v1 writer añade CPU | ADR específico+migración segura antes código, no permisos por este candidato. `/v1` y DTO M1 preservados |

| PF-N13 project_zip con metadata ByteRef; audio/stems/video/lyrics con metadata NULL u omitida; metadata_ref project omitida; operation/kind/payload/profile disconformes; Take/audio fabricados para Song sin tomas | INVALID antes de efectos; gate/reader no liberado: DEPENDENCY_UNAVAILABLE, sin output/prepared/final/Package. Parametrizar cinco parejas y verificar Song master NULL/takes [] sin rechazo por ausencia de Take |

| Criterio T-04 | Concreción revisable / pendiente real |
|---|---|
| Compatibilidad y golden por origen | §4.1/4.8: dispatch exacto, 22vectores,4fuentes golden con hashes verificables; golden v2/Artifact/Timeline/closure completos deberán emitirse en sus tareas tras ADR/schema |
| CA-12 | §4.6 bytes original, ZIP4roles48k/amplitud/offsets/common frames; pruebas codec/medio/alineación y lector independiente aún pendientes |
| CA-13 | §4.6 metadata/take/artwork/letra histórica solicitada; omit no embebe; combinación original+embedded explícita. Tags/lectores reales aún pendientes D-05/07 |
| CA-18 | §4.2/4.4/4.5: initial/context/binding/hash/duración/tokens single/composite inmutables, corrección hija; alignment de canción completa aún pendiente D-06 |
| CA-26 | §4.4 scene/time/audio/timing/features/fonts fijados e incertidumbre; implementación/karaoke/preview/export audiovisual pendientes D-07 |
| CA-36 | §4.5 closure completo, historia/roles/maps/metadata/rights/media/manifests/readers, biblioteca separada; Song sin Take conserva master NULL/takes [] y título/letra/portada/revisiones, export_project metadata_ref NULL sin Take/audio fabricados; export/import/restore reales pendientes D-08/09 |
| CA-38 | §4.7 IDs/path/custodia/receipts propios, dedupe/remap explícito sin overwrite; carreras/crash/commit pruebas futuras D-08 |
| CA-39 | §4.3/4.5 privacidad sin absolute/secret/live; material privado necesario retenido autorizado; inspección de paquete real pendiente |
| CA-48 | §4.1/4.2/4.5 derechos conjuntivos y datos veraces, CPU sin modelo/seed/ganador ficticio, historia byte-exacta; schema/code-first/API/ADRs antes producto |

## 5. Impacto por ruta real

Todas las rutas siguientes existen en el corte salvo los futuros schemas nuevos explícitos. Son impacto del diseño, no tareas descompuestas ni implementación autorizada por el actor.

| Ruta | Impacto futuro / límite |
|---|---|
| `packages/audio-post/audio_post/manifest.py` | Registro dispatch v1/CPUv2 exacto; validar output/private context sin reinterpretar v1. Artifact readers nuevos en módulo separado, no parchear schema histórico |
| `packages/audio-post/audio_post/private_context.py` | Lectura original privada por bytes/hash; no incorporar letra/foto en manifest/log ni sobreescribir context previo |
| `apps/server/app/snapshots.py` | SongCPUv2/bundle y cierre nuevo con lectores explícitos; `_project` v1 preservado y ningún backfill ficticio |
| `apps/server/app/worker/contracts.py` | ByteRef/paquetes/artifacts nuevos tipados, PostPlan1/autoridad inferencia originales intactos; no catch-all |
| `apps/server/app/worker/planning.py` | Uso de referencias versionadas del sujeto/operación, plan derivado N0; no inferencia inventada para CPU |
| `apps/server/app/worker/publications.py` | Lectores/package exactos por sujeto tras autoridad D-02/D-03 real; no-clobber/replay y fase final existente conservados |
| `apps/server/app/worker/execution.py` | Receipts de etapas efectivas; raw/CPU/upload/import/maintenance separados, sin claims como custodia |
| `apps/server/app/models/__init__.py` y `apps/server/app/migrations/versions/` | Datos D-03 únicamente migración aditiva aprobada; ningún enum Asset nuevo ni ampliación excepción ADR-0074 por D-04 |
| `apps/server/app/backup.py` | Biblioteca/cut/restore D-09 requiere nuevo contrato; backup SQLite actual no es prueba de backup media ni activación |
| `packages/contracts/manifest-v1.schema.json`, `song-v1.schema.json`, `timeline-v1.schema.json` | Compatibilidad byte/schema históricos; no alterar tipos/required para CPU/N0 |
| `packages/contracts/` nuevos schemas | Artifact/Package/prepared/TimelineV2/SceneN01/metadata/bundle: nombres y `$id` por reader definitivo tras ADR y código correspondiente; no creados en esta entrega |
| `packages/contracts/openapi.json`, `engine-v1.json`, `apps/server/app/api_models.py` | Regeneración code-first con su código futuro; paths/DTO M1 y engine /v1 sin cambios rompedores |
| `apps/server/tests/fixtures/creative/` | Fixtures históricas SHA intactas; nuevas fixtures v2/M3 en namespace distinto tras RED real; índices distinguien synthetic de integración |
| `apps/web/components/PlayerContext.tsx`, `GenerativeViz.tsx` | Reloj audio/scene compartida futura y bindings offline; no captura del estado web vivo como autoridad |
| `docs/arquitectura/convenciones.md`, `datos.md` y `docs/decisiones/` | Sólo ROOT adopta apéndices/ADR de §7 tras revisión; actor no escribe esos archivos |

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación / frontera |
|---|---|
| Confundir manifest2/song2/receipt1/Artifact1 por números | Registro exacto family+reader+version y hashes originales; rejects sin fallback |
| Reabrir CPUv2 cerrado mientras faltan bytes en snapshot | Reader CPUv2 liberado antes RED dependiente; siempre familia bundle1 nueva para M3, ningún schema2 redefinido |
| Artifact1 se vuelve wrapper genérico | Siete readers con campos comunes/especializados exactos, pares19 literales y refs schemas adoptados; desconocido/gate ausente falla |
| Colisión root.kind/seal_kind o JSON duplicado | D-03 FIX1 preservado; ninguno de esos campos se añade a envelopes/request/receipt; parsing duplicate antes hashmap |
| Hash circular package/manifest/final receipt | Package hashea prepared artifact sin publication_ref; final artifact fuera de members, receipt hashea package; readers preparados no serving |
| Export omite historia para pasar v1/cuota | Point-fixed closure+historia completa, sin truncación; cuotas D-08 mayores separadas o rechazo honesto |
| Original byte-exacto y embedding simultáneo | Incompatibilidad explícita, sidecar en original, derivado distinto para embedded |
| Import adopta por hash o remap toca originals | Receipt propio+mapa completo nuevo, no-clobber+CAS actual, history/owner source separado |
| Metadata privada filtra texto/foto/absolutos | Sólo payload privado autorizado, ByteRef exterior, inspección antes export; original inadmisible bloquea, no sanitización silenciosa |
| N0 parece validado por descripción | Pruebas de canción completa/timing/audio/frame/assets/fonts/codec/equivalencia reales, pendientes D-06/07 |
| Backup SQLite actual parece biblioteca recuperable | D-09 cut exclusivo+medios+restore ext4 nuevo+binding/rollback; trabajos históricos inertes |
| Nueva opción requiere más alcance que evaluación | Múltiples schemas/readers/paquetes nuevos; ROOT revisa riesgos de evaluación antes plan/código si excede alcance; sin estimar horas aquí |

## 7. Preguntas abiertas, apéndices y ADR específico

No quedan alternativas arquitectónicas abiertas: PF-O1 seleccionada y SongBundleM31 siempre nuevo para M3. Pendientes **de producto/contrato dependiente**, no permiso para ejecutar: schemas CPUv2/SongCPUv2 finales M2 y readers liberados, sin reinterpretación; perfiles D-05/06/07 y codec/font/tags/metrics; catálogos/cuotas/mapa D-08; cut/binding/restore/rollback D-09; gate D-11 artwork y T14 temporal. ROOT revalida head/code-first y reserva ADR específico antes de código incompatible. Ningún pending se completa con datos ficticios.

### Apéndice candidato para convenciones.md — extracción exclusiva ROOT

INICIO_APENDICE_CONVENCIONES_D04

Los formatos nuevos de producción usan lectores cerrados por family/reader/version; una versión desconocida o gate no liberado rechaza antes efectos. El número de versión no es global. Inferencia manifest1, CPUv2/SongCPUv2, timeline1 y sus bytes originales conservan semántica. M3 usa ProductionArtifact1/Package1 con7readers por sujeto cuando no cabe en familias históricas; no redefine CPUv2 ni añade inferencia ficticia a CPU/upload/import/maintenance. Las refs privadas D-02/D-03 y los11sellos `seal_kind` conservan campos/hashes propios. Un hash/receipt importado es historia, no autoridad activa.

TimelineV2/SceneN01 N0 liga VideoRevision/audio final/timing/context/features/fonts/perfil capturados, sin letra privada en el índice ni master actual como default. El reloj de audio y cuadro racional alimentan la misma escena temporal offline. Bytes v1/timeline1 no se convierten silenciosamente. Original conserva bytes y usa metadata sidecar; embedding exige export derivada cuando cambiaría original. Stems48k conservan4roles/amplitud/alineación común sin normalizar. Metadatos/lyrics usan la versión histórica solicitada; omit no embebe.

Paquetes privados conservan cierre completo de Song/historia/ancestros/roles/maps/refs/rights/media/manifiestos por versiones exactas. Ningún secreto, path absoluto, lease/PID/autoridad viva viaja en el paquete; letras/fotos necesarias sólo payload privado autorizado. Import revalida owner y usa receipt propio, mapa source→local completo y no-clobber/CAS; no dedup global por hash ni overwrite. Backup de biblioteca exige cut/SQLite/media juntos y restore/binding/rollback D-09, sin reactivar procesos históricos.

Export audio/stems/video/lyrics exige metadata_ref ByteRef production.export_metadata/1 ligado al Take efectivo. Export_project/project_zip exige metadata_ref NULL literal en prepared/final/Package, incluso con Takes; título/letra/portada/revisiones se recuperan por closure Songv1/SongCPUv2/SongBundleM31. Song válida master NULL/takes [] conserva historia sin metadata de Take ni Take/audio ficticios. Operation/kind/payload/profile deben coincidir con D-02; gate ausente bloquea antes efectos.

FIN_APENDICE_CONVENCIONES_D04

### Apéndice candidato para datos.md — extracción exclusiva ROOT

INICIO_APENDICE_DATOS_D04

Los datos de D-03 conservan las40tablas/11sellos/guards y FIX1: `root.kind` SQL intacto y `seal_kind` reservado sólo en sus schemas internos. D-04 agrega formats/readers, no columnas, tipos ORM ni excepción SQL. Asset no admite job/analysis/import/backup; Analysis original UNIQUE/data permanece inmutable. CPUv2 no se amplía a sujetos M3 por analogía. Import/backup usan capturas propias, preview temporal no crea Asset/Take ficticios.

Song con cierre CPU/historia mixta usa SongCPUv2 original de ADR-0074; Song sin CPU conserva Songv1. Todos los índices portables M3 usan **siempre** `production.song_bundle/1` como familia nueva que envuelve snapshot_ref y originals ByteRef, sin redefinir song1/song2. Closer conserva todos los takes/masters/ancestros, aristas/roles/maps, letras/context/tokens/revisiones, Analysis/Mix/artwork/vid/exports/presets/refs/metadata/rights/media/manifests y causalidad necesaria. Catálogo/proyección/mapa/cuotas D-08 sigue gate propio. Una proyección remapeada nueva posee IDs/hash propios y referencias a originals byte-exactos; no reescribe source IDs/owner/manifests ni crea inferencia del importador.

Package preparado→prepared artifact sin publication_ref→evidencia previa evita ciclo SHA; import/backup usa validación/maintenance_execution previa D-08/D-09 y no receipt final anticipado. Final receipt referencia package y artifact final referencia final receipt, fuera del package. Sólo final committed propio acredita visibilidad tras autoridad real/CAS/custodia. Historia imported de receipts/requests/planes permanece inerte sin tokens/leases/PIDs/custody viva. Biblioteca restaura en destino nuevo validado y activa BD/raíz juntas sólo D-09; pending reader/gate bloquea, no default/alias/rewriting históricos.

Export audio/stems/video/lyrics exige metadata_ref ByteRef production.export_metadata/1 ligado al Take efectivo. Export_project/project_zip exige metadata_ref NULL literal en prepared/final/Package, incluso con Takes; título/letra/portada/revisiones se recuperan por closure Songv1/SongCPUv2/SongBundleM31. Song válida master NULL/takes [] conserva historia sin metadata de Take ni Take/audio ficticios. Operation/kind/payload/profile deben coincidir con D-02; gate ausente bloquea antes efectos.

FIN_APENDICE_DATOS_D04

### ADR candidato específico sin número — extracción exclusiva ROOT

INICIO_ADR_CANDIDATO_D04

**Título:** Familias de publicación tipadas M3, dispatch multiversión y escena N0 portable.

**Estado propuesto:** propuesta. **Decisión arquitectónica:** ROOT por delegación explícita el2026-10-11, PF-O1; revisión/adopción canon separadas. **Número:** no reservado por este actor.

**Contexto.** ADR-0074 conserva manifiestos inferencia1/CPU2, snapshotsCPU2 y API M1. El corte code-first aún valida manifest1 y emite Song1; timeline1 describe montaje, no N0. D-02/D-03 fijan19pares/7sujetos y capturas/sellos/CAS tipados. Analysis/import/backup no caben en el manifiesto1 actual ni son Asset/Take ficticios. Un original cerrado no puede reescribirse para añadir esos sujetos, remap, privacidad o escenario.

**Decisión.** Adoptar PF-O1: readers family/version/reader exactos, referencias byte-exactas, envelopes Artifact1/Package1/prepared por7sujetos y ramas engine/cpu/upload/import/maintenance de evidence real. No hybrid como executor, ningún engine/seed de padre como ejecución. CPUv2 y SongCPUv2 originales cerrados; nuevo song_bundle1 **siempre** para índice portable M3, refiere snapshot1/2 sin modificación y closure/proyección D-08. TimelineV2/SceneN01 para N0 con audio/timing/context/features/pins/fonts/clock fijos. Metadata1 exclusiva de audio/stems/video/lyrics, ligada a take/letra histórica solicitada; export_project/project_zip exige metadata_ref NULL literal en prepared/final/Package y closure Songv1/SongCPUv2/SongBundleM31, incluso con Takes. Song válida master NULL/takes [] conserva título/letra/portada/revisiones sin metadata de Take ni audio/Take ficticios; operation/kind/payload/profile coinciden con D-02 y gate ausente bloquea antes efectos; original byte-exacto+sidecar, embedding derivado; stems4roles48k sin normalizar con offsets/frames comunes.

**Cierre/remap/privacidad.** Toda historia/cierre requerido por §4.5 conserva padres/roles/maps/maestro/declaraciones/refs/media/manifests/metadatos/rights. Catálogos D-08 y biblioteca D-09 conservan sus gates. Replay sólo receipt propio misma captura; no adopción por hash/ID/ruta, no-clobber/CAS y maps nuevos con originals/owners source separados. Operaciones import/maintenance no se convierten en inferencia. No live authority/leases/PIDs/secretos/paths absolutos; payload privado autorizado para letra/foto. Original inadmisible impide export completo sin reescribirlo.

**Documentos que cambia explícitamente.** Convenciones actuales describen sólo API sin versión y formatos/paths básicos: actualizar sólo la extensión multiversión D-04, conservando API aditiva ya autorizada ADR-0074. Datos actual describe Song1/timeline1/autoridad por Take: añadir la concreción M3 por sujeto, TimelineV2 y nueva familia SongBundleM31. La prescripción CPU2 de ADR-0074 no se invalida. No cambiar baseline/DTO M1/engine /v1 ni ampliar reconstrucción SQL.

**Alternativas descartadas.** PF-O2 manifiesto universalv3/proyección única, por reinterpretación de historia y reconciliación innecesaria. Sentinelas, alias por versión y JSON libre, por procedencia falsa y falta de reader. Sanitizar originales en export o remap, por romper byte-exactitud. Asset job/analysis/import/backup o Song de biblioteca artificial, por contradicción de D-03/baseline.

**Consecuencias/gates.** Nuevos schemas/readers/goldens concretos code-first, migraciones sólo aprobadas D-03 y comparación compatible previa CPU2. Package prepared elimina SHA circular y no autoriza serving. Perfils/métricas/codec/tags/fonts D-05/06/07, catalog/identitymap/cuotas D-08, mantenimiento D-09 y validación runtime/crash/concurrencia quedan pendientes. Aprobación documental no acredita ejecución, producto, remap ni restore.

**Umbral.** Cierra alternativa real y afecta contracts/snapshots/worker/render/import/backup: requiere ADR específico y apéndices adoptados antes de schemas/código. ROOT reserva número y enlaza cadena; este actor no reserva ADR canon.

FIN_ADR_CANDIDATO_D04

### Verificación documental y cese

Verificación ejecutada: «lectura: production-format-contract.md → cada sujeto tiene formato/lector; v1 cerrado e historia sin reescritura». Lectura del candidato e inspección estática comprobaron §4.1/4.2 (registro literal7sujetos/readers/fieldsets), §4.4 (timeline/escena), §4.5/4.7 (historia/originals/remap), §4.8 (21vectores) y §4.9 (criterios/fallos). Comparación PowerShell `Get-FileHash -Algorithm SHA256` contra **cada** entrada `release-root.receipt.json.snapshot_sha256` antes y después:128fuentes,0diferencias. Comparación contra fixture-index de los22archivos, tamaño y SHA:22iguales,0diferencias.

Salida real anterior a incorporar este bloque: `readonly_sources=128; readonly_mismatches=0; fixture_index_entries=22; fixture_mismatches=0; numbered_sections=7; subject_readers=7; golden_origin_vectors=21; negative_groups=12; placeholders=0; extraction_markers=6; selection=PF-O1; result=PASS documental; no runtime`. La primera salida mostró una enumeración PowerShell de128conteos unitarios al pedir `.Count` de PSObject.Properties; se corrigió mediante `@(...).Count`, sin alterar las comparaciones SHA ni los archivos. No se trata de prueba de reader/schema funcional ni import/export/render/restore. La matriz de CA establece concreciones y gates futuros; las fixtures nuevas v2/M3 no existen en este corte y no se fabrican como producto ejecutado.

El actor cesa escritura después de comprobar nuevamente el candidato final y las128fuentes. El manifiesto before/after completo es la lista SHA del release más sus comparaciones0; ROOT conserva receipt de congelación/hash final fuera del contenido autorreferente y realiza revisión/QA/adopción. Source propuesta única: este archivo. No se atribuye DONE a implementación T-04 ni al hito por su redacción. TDD n/a: prosa. ADR candidato no numerado; no canon ni ledger escrito por el actor.

Changelog propuesto: «Concreta formatos/lectores M3 por siete sujetos, multiversión con originales byte-exactos, escena N0 y cierre portable completo; distingue CPU/upload/import/mantenimiento, rights y remapeo sin sobrescritura. Conserva D-02/D-03/ADR-0074; aceptación funcional y producto permanecen pendientes».

### FIX1 documental — metadata de proyecto y legibilidad

ROOT eligió esta corrección después de revisión1: B01 Important y A01 Minor, sin reapertura de PF-O1 ni cambio D-02/D-03. La evidencia anterior de 21 vectores y 12 grupos negativos corresponde al candidato original; permanece histórica. FIX1 añade PF-G05-P0/PF-N13 y concreta PF-G05-X. No acredita ejecución de sus nuevas fixtures.

Verificación ejecutada de nuevo: «lectura: production-format-contract.md → cada sujeto tiene formato/lector; v1 cerrado e historia sin reescritura». La lectura verificó siete subjects/readers, cinco parejas export, metadata_ref siempre presente y cerrado por kind, prepared/final/Package coherentes, cierre Song sin Take, reader metadata de medios sin ampliación, CA-13 intacto y CA-36 explícito. También verificó la propagación dentro de los dos apéndices y el ADR candidato. A01 separa preparación previa, omisión de campos de ejecución final y conservación de refs root en tres frases; el DAG y la prohibición de serving permanecen.

Salida real FIX1: `readonly_sources=129; readonly_mismatches=0; original_128_sources=128; original_128_mismatches=0; fixture_index_entries=22; fixture_mismatches=0; subject_readers=7; export_pairs=5; golden_origin_vectors=22; negative_groups=13; extraction_markers=6; historic_verification_21_12_preserved=true; metadata_fieldset_unchanged=true; song_without_take=true; no_runtime=true`. Evidencia y hashes before/after completos: namespace privado `documenter-fix1/` de esta entrega. El hash final se conserva fuera de la fuente para evitar autorreferencia.

El arquitecto anterior terminó READONLY por restricciones de artifacts: verificó 130 SHA sin diferencias, no escribió fuente ni consumió intento de revisión. Esta corrección la escribe el actor documenter autorizado exclusivamente en el snapshot. ROOT regenera los derivados y conserva en exclusiva canon, ledger, CAS, Git y adopción. TDD n/a: prosa; readers/schemas/export/import/render/restore, medios, GPU y aceptación de producto siguen pendientes de sus tareas reales.
