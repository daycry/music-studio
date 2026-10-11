---
estado: aprobado
eleccion_ROOT: ratificada; revisión1 y QA documental403/403 completadas; adoptada por ROOT
fecha: 2026-10-11
iniciativa: m3-produccion-portada-video-letra
tarea: T-02
decision: D-02
opcion_elegida: PR-O1
autoridad: ROOT bajo delegación vigente del propietario; elección explícita 2026-10-11T18:10:35.263982+00:00
adr: ADR-0082 aceptada por ROOT tras revisión y QA documental
namespace: privado del server; especificación normativa de contratos futuros
tdd: "n/a: prosa; sin implementación runtime"
generacion:
  fuente: estimado
  tokens_reales: null
  eur: null
  nota: No se ejecuta medidor propio; consumo real desconocido.
---

# ProductionRequest y autoridad por sujeto — D-02

ROOT elige PR-O1: envelope privado común, receta única y autoridad discriminada por resultado. La elección cierra D-02 documentalmente para revisión; no cierra T-02, ningún gate de integración ni función M3. La adopción exige revisión A/B, QA independientes y acta ROOT. No se atribuye lectura o ratificación personal al propietario.

O1 de [ADR-0080](../../decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md) y D-12 del [contrato de dependencias](dependency-contract.md) siguen vigentes. [Plan](improvement-plan.md), [spec](spec.md) y [test-plan](test-plan.md) conservan sus criterios. PR-O2, contratos por familia, se descarta porque duplica obligaciones de captura/CAS/recovery en siete lectores; su independencia de versiones no compensa esa deriva inicial. PR-O1 conserva evidencias específicas y gates cerrados por rama.

La elección y alternativas son evidencia privada de ROOT en las rutas **repo** `.cache/dev-cycle/m3/production-request-t02-concretion-20261011/{choice-root.receipt.json,options.md,options.json}`. Son referencias de auditoría local, no links relativos desde este documento ni payload portable. SHA de options.md: `03981fff3ee9816eb9b9c64088e51669462d5460f04cec181d90ed08de969c5f`; options.json: `e21cae9c0ca1f2dcd188f52058eed03e9ac2a83c2f846b02e44d7773320bafa6`. El candidato ADR vive sólo en ese namespace, sin número reservado.

## 1. Fronteras y disponibilidad

Sólo el server escribe SQLite. Job/job_dependency y locks/carriles actuales siguen siendo la cola: GPU1, CPU2, remote opcional apagado. No hay runner paralelo ni agregado durable de sesión de producción. Un modelo reside en VRAM; la conformidad y el binding/admisión/custodia se acreditan antes de usar su operación. Engines siguen [contrato `/v1`](../../arquitectura/contrato-engines.md), salida cruda en tmp e intento real, sin conocer sujetos de dominio.

`PostPlan.version=1` y PublicationAuthority de M1 mantienen inferencia real. No se les añaden ganador, terminal, modelo o seed ficticios para encajar CPU/upload/export/backup. ProductionRequest1, ProductionRecipe1 y ProductionReceipt1 son familias privadas nuevas: el número1 no significa manifest1, song1, private_context1, CreativeRequestV1 o `/v1`. Un descriptor, DTO, hash, ruta o pin acredita contenido/forma dentro de su alcance; no permiso, custodia, derechos legales ni capacidad runtime.

El corte ROOT tiene78fuentes. M1 formal0/17, M2=4/30, M3 T-01 contractual1/42 y funciones de producto0. El contrato K1 aceptado y su implementación candidata privada con FIX1 no acreditan store nativo, ext4, published, grant o runtime. Si un seam no está liberado por ROOT para operación/versión/SHA, queda bloqueado conforme D-12 aunque este contrato sea válido.

## 2. Tipos, captura y límites ratificados

Todos los objetos nuevos son cerrados: campos enumerados obligatorios salvo `?`; un optional ausente no significa default al leer. No se aceptan extras, duplicate keys, bool como int, coerción de string/int, NaN/Infinity ni sustitución silenciosa de versión. Enums son sensibles a mayúsculas. IDs ULID con gramática existente; SHA256,64hex minúsculos. `Label` tiene1–512caracteres Unicode; `UInt` es int estricto>=0, sujeto a su lector/cuota cuando aplica; `Revision` es int estricto1..2^63−1; fechas ISO8601 UTC; tiempos segundos finitos no negativos. Sin secretos, credenciales, scripts, comandos, paths personales o transporte ejecutable en recipe.

| Límite nuevo | Valor exacto | Aplicación |
|---|---|---|
| Request JSON canónico UTF-8 | ≤2097152bytes | Antes de enqueue |
| Recipe JSON canónico UTF-8 | ≤1048576bytes | Antes de hash/captura final |
| Profundidad JSON | ≤32 | Raíz objeto profundidad0; cada objeto/lista contenido añade1; escalar conserva la profundidad de su posición |
| Sources / parents / required_roles | Cada lista≤64 | Listas ordenadas; duplicados de identidad/rol donde se exige unicidad rechazan |
| Profiles | ≤16referencias | Cada payload efectivo canónico≤65536bytes; presupuesto agregado de recipe también aplica |
| Lyrics versions | ≤64 | Texto de cada versión≤32768caracteres Unicode; aplica además límite de bytes agregado |
| Labels / paths relativos | ≤512 / ≤1024caracteres Unicode | Path POSIX confinado según lector seguro existente, sin traversal/alias/reservados |
| Revisiones monotónicas | ≤9223372036854775807 | Overflow rechaza; no wrap/reset |

Captura nueva: validar, copiar valores efectivos sin aliases mutables, serializar JSON UTF-8 sin BOM, `ensure_ascii=false`, claves ordenadas y separadores`,`/`:`, números finitos; SHA sobre esos bytes exactos. Recipe se serializa/hash por separado; request contiene ese valor y su SHA y posee sus propios bytes/SHA. El request hash se guarda en contexto durable, no dentro de sí mismo. Repetir captura con el mismo request_id exige iguales bytes/hash e identidades: si difieren, conflicto, no overwrite.

Overflow se rechaza **antes de enqueue**, sin truncar texto, fuentes o roles, sin chunking implícito y sin modificar la petición efectiva. Estos topes son de transporte/captura nuevos; no duración musical, GPU, media, storage ni catálogo. Catálogos/medios grandes son artefactos externos tipados/hasheados con cuotas D-08/D-09 distintas. No se reinterpreta ni reescribe historia para imponer límites nuevos.

## 3. Envelope, receta y referencias: única ubicación autoritativa

| Campo | Tipo / versión | Owner de escritura | Invariante |
|---|---|---|---|
| `kind` | literal `production_request` | Server | Sólo lector privado M3 |
| `schema_version` | literal int1 | Server | Reader dispatch exacto; versión desconocida rechaza |
| `request_id`, `job_id`, `owner_id` | ULID | Server autenticado | Inmutables; owner acreditado por sesión/filas, nunca por afirmación del cliente |
| `scope` | SongScope o LibraryScope | Server | SongScope `{kind:song,song_id:ULID}`; LibraryScope `{kind:library,binding_ref:BindingRef}`. Sin canción ficticia en mantenimiento |
| `operation` | enum de19parejas §4 | Server | Ningún dispatch genérico por path/handler del cliente |
| `subject` | `{kind:SubjectKind,result_key:ULID}` | Server | kind=asset/analysis/artwork/render/export/import/backup; result_key reservado y estable sólo dentro replay |
| `recipe` | ProductionRecipe1 | Capturador server | Única autoridad de fuentes/selección/valores privados |
| `recipe_sha256` | SHA256 | Capturador server | Coincide con bytes capturados de recipe; no permiso runtime |

ProductionRecipe1 es objeto cerrado con `schema_version=1`, `sources`, `parents`, `lyrics`, `rights`, `profiles`, `revisions`, `execution_selection`, `parameters` y `required_roles`. Todos estos campos están **sólo dentro recipe**, nunca como sidecars o copias top-level. Lista vacía sólo si la pareja lo permite. `parameters` es una de las ramas enumeradas en §4, no dict libre. BindingRef es referencia privada cerrada `{reader_version:Revision,binding_id:ULID,sha256:SHA256}` a evidencia capturada propia. El reader específico/binding activo es gate D-09; su ID/hash no concede admisión.

| Campo recipe / tipo cerrado | Contenido normativo y alcance |
|---|---|
| `sources: SourceRef[]` | `{kind,id,owner_id,role,sha256,media_type,bytes,evidence_ref}`. kind enum asset/upload/analysis/artwork/render/export/package; id ULID; role Label permitido por pareja; media_type Label validado por lector de la rama; bytes UInt. `evidence_ref` HistoricRef o CapturedRef. Pertenencia y bytes reales se revalidan. No path en recipe. |
| `parents: ParentRef[]` | `{kind:take,id:ULID,song_id:ULID,owner_id:ULID,root_id:ULID,manifest_ref:HistoricRef,audio_sha256:SHA256}`. Orden preservado, identidades únicas; antecedentes reales, no cómputo del derivado. No padres Take ficticios para artwork/import/backup. |
| `lyrics` | `{kind:none}` o `{kind:single,versions:[LyricsRef],bindings:[]}` con exactamente1versión, o `{kind:composite,versions:LyricsRef[],bindings:CapturedRef[]}`. LyricsRef `{id:ULID,sha256:SHA256,text:string,declaration:own|assistant|public_domain|licensed}`. Texto/hash y declaración histórica exactos; bindings tipados de cierre M2/M3, no offsets inventados. None sólo si no se consume letra. |
| `rights` | `{declarations:RightsRef[],commercial_use:bool}`. RightsRef `{ref,kind:audio|image|lyrics|parent|tool|model,sha256:SHA256,declaration:own|assistant|licensed|consented|public_domain,real_person:bool,consent:self|consented|n_a,commercial_use:bool,evidence_ref:CapturedRef}`. ref es `{kind:entity,id:ULID}` para fuente/letra/padre, o `{kind:pin,id:Label}` para tool/model: no ULID ficticio de un pin. Cada fuente/antecedente consumido y tool/model efectivo queda cubierto; declaration depende de su clase histórica: assistant sólo lyrics, consented sólo medio con consentimiento; tool/model usa licensed y evidencia de licencia/pin, sin declaración humana inventada. Foto real exige self/consented; tool/model exige real_person=false y consent=n_a. |
| `profiles: ProfileRef[]` | `{role,ref:CapturedRef,effective:TypedValue}`. role enum mix/audio_export/stems_export/features/alignment/artwork/render/portable/library; único por rol usado. TypedValue tiene reader, versión y payload **cerrado por ese reader ratificado**; no JSON arbitrario. Captura valor efectivo/hash, no alias mutable de preset. Gate de reader pendiente bloquea rama. |
| `revisions: RevisionRef[]` | `{kind,id,reader_version,revision,sha256}`; kind enum mix/lyrics_timing/video_project/analysis/preset; id ULID, reader_version Revision. VideoProject usa rev int>=1 vigente; otras entidades deben coincidir con tipos/valores de lector propio ratificado D-03, nunca defaults/coerción. `revision` debe ser Revision bajo lector nuevo; un histórico no compatible usa HistoricRef y gate de compatibilidad previo. |
| `execution_selection` | EngineSelection / CpuSelection / UploadSelection / MaintenanceSelection, abajo |
| `required_roles: Label[]` | Conjunto cerrado, orden capturado, únicos. Required de inputs y outputs se comprueban por separado; roles de output en esta lista. Conteos exactos por pareja; no role desconocido ni sustitución FLAC→WAV por retag |

HistoricRef es `{family:manifest|song|creative_recipe|composition_plan|private_context|input_receipt|timeline,version:Revision,sha256:SHA256}`: family+version despacha lector exacto, conserva bytes originales y semántica. No convierte receipt2 en manifest2. CapturedRef es `{family:profile|measurement|revision|catalog|closure|binding|execution|publication,reader:Label,version:Revision,sha256:SHA256}`; reader proviene del registro cerrado server ratificado para la pareja, nunca del cliente; desconocido/gate ausente bloquea. TypedValue `{reader:Label,version:Revision,payload:<objeto del schema cerrado del reader>}` debe coincidir con el ProfileRef y su SHA canónico. Esa referencia es seam deliberado, no catch-all que permita ejecutar sin concretar schema.

`commercial_use = AND(declarations consumidas)`; incluye entradas/padres/letra/herramientas y modelo sólo si realmente interviene. Falta declaración aplicable bloquea, no se interpreta true. Un false restringe el resultado. Una conjunción true no demuestra permiso legal: evidence/licencias/rights siguen comprobables. Rights privadas viajan sólo por payload autorizado; logs/DTO públicos no contienen letra, prompts, fotos, credenciales ni paths privados.

### Selección efectiva cerrada

| Rama | Campos | Reglas |
|---|---|---|
| EngineSelection | `kind=engine`, `capability:Label`, `descriptor_ref:CapturedRef`, `model_id:Label`, `model_revision:Label`, `mode:Label`, `parameters_ref:CapturedRef`, `seed?:UInt` | Selección local verificada por capacidad/features; descriptor/params congelados y schema cerrado propio; seed sólo donde descriptor lo declara. No referencia ejecutable arbitraria. Intento/terminal real se incorporan después, no al recipe |
| CpuSelection | `kind=cpu`, `handler:Label`, `handler_version:Revision`, `tools:CapturedRef[]` | Handler del registro cerrado de pareja; tools/pins reales y licence; no engine/model/seed/ganador. Audio render usa servidor sin torch, no inferencia dummy |
| UploadSelection | `kind=upload`, `upload_id:ULID`, `sha256:SHA256` | Debe corresponder SourceRef upload autorizado con derechos/consent; no model/seed/job_attempt |
| MaintenanceSelection | `kind=maintenance`, `action=backup|restore|activate`, `binding_ref:BindingRef`, `policy_ref:CapturedRef` | Coordinador propio exclusivo; coherencia scope/binding/action; política cerrada D-09. No permiso por snapshot binding |

`parameters_ref` no copia params fuera recipe: referencia dentro selección apunta a captura privada cerrada de parámetros efectivos. Capturas referidas requeridas forman cierre privado de request y se conservan inmutables. Un cambio de descriptor/preset tras la captura no retargetea ni revalida retroactivamente la selección histórica.

## 4. Matriz de19parejas: resultado, parámetros y gates

Se usan parámetros cerrados de dominio: RefID=ULID, revision=Revision, hash=SHA256. Campos de una rama nunca se aceptan en otra. No se completa información ausente desde el estado actual. Valores de roles exactos, perfiles efectivos y readers indicados pendientes se ratifican en sus gates **antes de su RED**, y la rama no se ejecuta entretanto.

| operation / subject.kind | `parameters` cerrado y captura obligatoria | Unidad / owner / terminal / gate |
|---|---|---|
| separate_stems / asset | `{take_id}`;1fuente audio master del Take padre; selección engine | Set exacto4roles vocals/drums/bass/other, assets con `subject_type=take`. Receipt raw real seguido de publicación del set completo; D-05 y capacidad real |
| mix_preview / asset | `{mix_revision_id}`; stems, perfil mix y RevisionRef exactos | Temporal privado job con receipt/expiry/invalidation, **sin** Asset.subject_type job ni Take. CPU receipt más autorización de serving temporal; D-03/D-05 y contrato temporal T14 |
| extract_features / asset | `{audio_source_id}`; audio final/hash, perfil features ventana/hop/timeline | Derivado del Take/audio autorizado; roles exactos del reader D-07. CPU medido + unidad completa; no medir otro master |
| analyze / analysis | `{take_id,method:beats|sections|key|loudness}`;1audio hash y método/pin |1resultado del método, success/failed/missing honestos; engine o CPU según capacidad. Evidence textual en sections se marca textual y no medición; D-03/D-04/D-06 |
| align_lyrics / analysis | `{take_id}`; audio/hash + lyrics single/composite y perfil alignment |1resultado inicial lyrics_timing, binding de fragments/offsets reales; engine real; D-06 y conformidad de canción completa |
| correct_lyrics_timing / analysis | `{timing_revision_id}`; RevisionRef padre, audio/hash/letra/bindings originales y perfil correction cerrado | Nueva revisión timing de tokens estables; CPU receipt no reescribe audio/texto/análisis. ProfileRef alignment conserva edits cerrados; D-03/D-06 |
| generate_artwork / artwork | `{kind:cover|keyframe|background}`; perfil artwork workflow/pins/params, rights |1Artwork o set explícito requerido; engine raw → commit Artwork/assets; no elegir Song cover automáticamente; D-04/D-11 |
| edit_artwork / artwork | `{kind:cover|keyframe|background,reference_source_id}`; referencia imagen autorizada + perfil cerrado/rights | Artwork nuevo con antecedente; capability edit gate separado de generate; D-11 |
| attach_artwork_upload / artwork | `{kind:cover|keyframe|background,upload_id}`; source upload exacto | Artwork source=upload, receipt copia/validación real, sin engine/model/seed ficticios. Derechos/consent antes enqueue; D-04 |
| render_n0 / render | `{video_project_id}`; RevisionRef video_project con timeline rev/hash; audio final, timing/artwork/features/perfil render | Render propio + assets del Render; CPU/browser/FFmpeg real. Plan derivado conserva timeline autoridad; D-03/D-04/D-07 |
| export_audio / export | `{kind:audio,target:original|streaming|broadcast|podcast}`; audio/mix y perfil audio_export | Export propio; original conserva bytes. Destinos miden final decodificado; ganancia constante/soxr, objetivo imposible falla. D-05 y D-04 |
| export_stems / export | `{kind:stems}`; set stems cerrado y perfil stems_export | Export ZIP completo, amplitud/alineación comunes; conversión sólo explícita de perfil; CPU receipt; D-05/D-04 |
| export_video / export | `{kind:video,render_id}`; Render committed autorizado + perfil render/export | Export propio de bytes finales acreditados; no declara nuevo render por copiar; D-07/D-04 |
| export_lyrics / export | `{kind:lyrics,format:lrc|srt,timing_revision_id}`; lyrics histórica/bindings y RevisionRef timing | Export propio; texto y tiempos exactos, missing no palabra inventada; CPU receipt; D-06/D-04 |
| export_project / export | `{kind:project_zip}`; cierre/root históricos + perfil portable | Export paquete completo con materiales privados autorizados, versions/rights/linaje; sin authority activa. D-04/D-08 |
| import_project / import | `{package_source_id}`; catálogo/cierre/versiones/rights y perfil portable | Intención/receipt por paquete: transacción publica cierre íntegro, no parcial. Scope song_id destino reservado propio, aún no fila si nueva; source→local separados. D-08 |
| backup_library / backup | `{action:backup}`; LibraryScope/binding, perfil library | Mantenimiento exclusivo, SQLite nativa y catálogo/medios del mismo corte; receipt cut/paquete propio; D-09 |
| restore_library / backup | `{action:restore,package_source_id}`; paquete completo y binding destino nuevo | Biblioteca nueva ext4 propia, integridad/FK/FTS/media/reproducción; jobs históricos inertes; D-09 |
| activate_library / backup | `{action:activate,restoration_ref:CapturedRef}`; restore acreditado, binding previo/nuevo capturados en perfil library | Binding raíz/BD juntos mediante intención durable y rollback; backup restaurable/exclusividad; D-09. No VHDX activo copiado |

Roles de salida distintos se expresan en `required_roles` del recipe. Para filas sin medio (Analysis), el rol de resultado es el kind/método de la fila; sus archivos crudos siguen privados y no se inventa Asset.subject_type analysis. Import y backup son sujetos de operación privada, **no nuevos enums ORM**. Si una representación persistente no cabe, D-03 decide migración adicional; D-04 formato nuevo y reader antes del RED. D-02 no extiende SQL por analogía con ADR-0074.

Los nombres de rol conceptual de stems vocals/drums/bass/other se proyectan a Asset.role `stem:vocals`/`stem:drums`/`stem:bass`/`stem:other`, siguiendo la convención histórica `stem:*`. El engine_role lo determina su descriptor ratificado; no se presume idéntico a asset_role. La validación conserva ambas namespaces y rechaza incoherencia sin retag implícito.

Casos con letras compuestas requieren bindings tipados realmente existentes; lyrics composite sin reader/bindings autorizados bloquea. No se infiere asociación por longitud, no se trunca a180s. La duración completa/cohorte y cada métrica musical/visual pertenecen a gates reales, no al tamaño máximo del request.

## 5. Contexto de ejecución, intención y CAS

El contexto runtime se mantiene **fuera del recipe/envelope**: `intent_ref:ULID`, `expected_revision:Revision`, `expected_state`, `request_sha256`, `execution_id:ULID`, `execution_ordinal:Revision`, refs a binding/lease/custodia vivos y evidencia adquirida por el server. No es autoridad importable, transportada por cliente ni exportable en paquete. Ref a lease no es capacidad activa: adquisición/revalidación real obligatoria. No se pone process/PID/lease/token en manifiesto público ni restore los reactiva.

La intención lógica por unidad tiene `{intent_id,owner_id,scope,request_id,request_sha256,recipe_sha256,subject,result_key,state,revision,active_revision_id}`; ids ULID; SHA/tipos anteriores; state enum reserved/prepared/committed/failed/cancelled; revision inicial1. El contenido de active_revision es inmutable: `{revision_id,intent_id,execution_id,execution_ordinal,request_sha256,expected_revision,result_evidence_ref,package_ref?}`; evidence/ref siempre del sujeto/executor real. D-03 fija persistencia/checks reales; los nombres lógicos no se anuncian como tablas existentes.

Transición CAS exige coincidencia simultánea de intent_id, owner/scope, request/recipe hashes, result_key, revision y active_revision_id/estado esperado, además de autoridad viva, cancel observado, custodia y binding/admisión adecuados. Se actualiza revisión monotónica sin overflow; si pierde CAS, no efecto/publicación ni overwrite. Leer la fila/hash correcto en el pasado no sustituye CAS actual. La revisión del intento es distinta de mix/timing/VideoProject; usar Song revision global no basta.

Intención durable se reserva **antes del primer efecto**; preparación/rename/no-clobber se registran antes de commit. Una unidad ready/committed es inmutable. Retry explícito de failed/cancelled sólo con políticas/gates, custodia reconciliada y CAS: nueva ejecución/ordinal y active_revision, misma captura original y resultado reservado si aún no committed; resultados anteriores y semillas/índices reales se conservan. Nueva acción/captura o resultado distinto usa request_id/result_key nuevos, no overwrite.

Un consumidor sólo reutiliza resultado committed con recibo propio y contexto/autoridad/bytes acreditados. No dedup global por contenido, no adoptar archivos ajenos y no publicar por path/hash. Artwork selection o master promotion son acciones explícitas/CAS aparte; publicar un derivado no las dispara. Una modificación posterior de Song/master/preset deja la captura intacta; eliminar/perder permiso de una fuente sí puede bloquear autoridad vigente, sin sustituirla por otra.

## 6. ProductionReceipt1, terminales y serving

| Campos comunes cerrados | Tipos / regla |
|---|---|
| `kind`, `schema_version`, `receipt_id` | kind enum engine_raw/cpu_result/upload_result/publication/import/maintenance; int1; ULID |
| `owner_id`, `scope`, `request_id`, `request_sha256`, `recipe_sha256`, `subject` | Identidad exacta congelada; mismo result_key; server valida pertenencia |
| `execution_id`, `execution_ordinal` | ULID / Revision; ejecución real, no JobAttempt dummy para CPU |
| `outcome` | succeeded/failed/cancelled; fallo/cancel conserva código cerrado; failed/missing Analysis no se envuelve como publication success |
| `evidence` | Si outcome=succeeded, rama cerrada según kind de tabla siguiente. Si outcome=failed/cancelled, FailureEvidence cerrada indicada después; no inventa campos de éxito |
| `artifacts` | Inventario de medios del resultado: `{role,path,sha256,media_type,bytes}`. Path relativo seguro y resolver runtime propia; SHA/tipos anteriores; conjunto exacto requerido, sin propio manifiesto/recibo autorreferente |
| `error_code?`, `finished_at` | Código cerrado §7 aplicable / UTC; error_code obligatorio para failed/cancelled y ausente para succeeded; no traceback, texto privado ni permiso importable |

| kind y evidence obligatoria | Terminal que acredita y el que no acredita |
|---|---|
| engine_raw | `{attempt_id:ULID,ordinal:Revision,terminal_seq:Revision,terminal_sha256:SHA256,provenance_ref:CapturedRef}`; seq/attempt son los reales de `/v1`. Sólo terminal engine raw. Nunca import/post/publicación |
| cpu_result | `{plan_ref:CapturedRef,tools:CapturedRef[],measurements:CapturedRef[]}`; ejecución server/hijo propietario real. Artefactos/mediciones propios y bindings a inputs/output. No atribuye inferencia a los modelos de padres |
| upload_result | `{upload_id:ULID,source_sha256:SHA256,copy_sha256:SHA256,rights_ref:CapturedRef}`; valida copia y derechos reales. Sin engine/model/seed |
| publication | `{intent_id:ULID,intent_revision:Revision,execution_receipt_ref:CapturedRef,package_ref:CapturedRef,committed_at:UTC}`; entidad/asset/state/receipt de unidad en commit SQLite acreditado. No prueba sola barreras/ext4 |
| import | `{intent_id:ULID,intent_revision:Revision,package_ref:CapturedRef,catalog_ref:CapturedRef,closure_ref:CapturedRef,identity_map_ref:CapturedRef,committed_at:UTC?}`. succeeded sólo tras cierre validado/promovido y commit indivisible. Mapa identity explícito incluso sin remap; D-08 fija schema, no reescribe originales |
| maintenance | `{intent_id:ULID,intent_revision:Revision,action:backup|restore|activate,cut_ref:CapturedRef,binding_ref:BindingRef,package_ref:CapturedRef,validation_ref:CapturedRef,rollback_ref:CapturedRef?}`; evidencia real por acción. Activate requiere rollback_ref; restore/activate cut conserva ventana exclusive propia, no supuesto snapshot de BD/media vivo |

FailureEvidence es `{boundary,observed_state,prior_evidence:CapturedRef[]}`. boundary enum capture/resolver/send/raw/post/render/prepared/rename/commit/serving/cleanup/import/backup/restore/activate; observed_state enum failed/cancelled/unknown. Registra sólo referencias existentes; ningún committed_at, copy_sha256, cut_ref o package_ref inexistente se fabrica para un fallo. artifacts de un receipt fallido/cancelado sólo enumera parciales propios acreditados y privados, nunca autoriza serving. Un terminal engine error/cancelled real se conserva como prior_evidence de intento/seq/SHA; outcome failed no se usa para negar un committed ya acreditado. Un error antes de enqueue/captura válida es rechazo sanitizado, sin inventar ProductionReceipt/request/execution durable.

Success de engine o CPU no es success de publicación. Job agregado concluye cuando sus unidades tienen terminales durables, sin convertir resultados mixtos o fallidos en éxito musical. Un resultado independiente committed permanece válido aunque otro falle; dentro de required role set/import closure no hay publicación/serving parcial.

Custody UNKNOWN se conserva separadamente del terminal: bloquea nuevos efectos, publicación, serving, cleanup y liberación de slot/staging hasta reconciliación acreditada. No genera failed/succeeded inventados. Temporal preview sólo se sirve con receipt/context privado, pertenencia, expiry/invalidation, CAS y custodia vigentes; nunca una ruta suelta.

Cancel antes del commit impide nueva publicación; efectos previos propios se reconcilian bajo intención sin borrar ajenos. Un commit durable ya ocurrido **gana** ante cancel tardío o respuesta perdida: se reproduce exactamente ese terminal/recibo, no se degrada a cancelled, no se regenera ni se repite commit. Ante acuse perdido se reconcilia el mismo intento; reinicio del engine en memoria no prueba inexistencia de efecto. Sólo reintento explícito con nueva ejecución y autoridad puede empezar trabajo nuevo después de reconciliar.

## 7. Fallos por frontera y respuestas cerradas

Los códigos siguientes son **privados M3 futuros**, no cambios de `/v1` ni ProblemDTO M1. `PRODUCTION_INVALID`, `PRODUCTION_VERSION_UNSUPPORTED`, `PRODUCTION_LIMIT_EXCEEDED`, `PRODUCTION_IDENTITY_CONFLICT`, `PRODUCTION_RIGHTS_REQUIRED`, `PRODUCTION_DEPENDENCY_UNAVAILABLE`, `PRODUCTION_SOURCE_MISMATCH`, `PRODUCTION_CAS_CONFLICT`, `PRODUCTION_CUSTODY_UNKNOWN`, `PRODUCTION_COLLISION`, `PRODUCTION_PACKAGE_INVALID`, `PRODUCTION_NOT_CONFORMANT`, `PRODUCTION_CANCELLED`, `PRODUCTION_INTERNAL`. Mensajes públicos sanitizados; errores internos se registran sin payload privado. API code-first futura concreta su proyección sin alterar DTO M1.

| Frontera | Caso y resultado requerido | Autoridad que puede reconciliar |
|---|---|---|
| Capture/admission | Tipo/pair/extras/duplicado/version/overflow inválido: código correspondiente, sin enqueue/efecto; rights ausentes: RIGHTS_REQUIRED | Server autenticado, readers cerrados y captura nueva; nunca truncado ni defaults actuales |
| Resolver | Owner/fuente/hash/revisión discrepante: SOURCE_MISMATCH; capacidad/reader/gate no liberado: DEPENDENCY_UNAVAILABLE | Captura histórica + filas/bytes reales y gate por operación/SHA |
| Send/ACK | ACK perdido: conservar request/attempt, reconcilia mismo ID/seq; estado no acreditado bloquea nuevo envío | Intento real/ledger server; no inferir ausencia de estado en engine reiniciado |
| Raw | Terminal hash/seq/bytes/roles no coinciden: SOURCE_MISMATCH o PACKAGE_INVALID; no adoptar raw ajeno | Ganador engine real, tmp propio/custodia y fuentes capturadas |
| Post | Plan/tool/medición faltante: DEPENDENCY_UNAVAILABLE; no conforme medido: NOT_CONFORMANT; no fabricar output/engine | Ejecución CPU propia y reader/medición real; recipe/plan/output binding |
| Render | Timeline/audio final/timing/features no ligados o codec/font/browser sin gate: bloqueo antes render/commit | VideoProject revisionado y plan derivado; nunca web viva ni master actual |
| Prepared/rename | Intent/CAS vencido: CAS_CONFLICT; final ocupado por ajeno: COLLISION. No-clobber y registro de efecto propio | Intent/result_key vivos, paquete exacto, binding/custodia real |
| Rename→commit | Crash con medio propio promovido sin commit: reconciliar efecto/intención; no servir ni regenerar. Archivo existente sin authority no se adopta | Evidencia durable propia preefecto + CAS actual; FS/SQLite no transacción conjunta |
| Commit→ACK | Commit durable/ACK perdido o cancel tardío: mismo receipt/terminal íntegro, sin doble publicación | Intención committed y paquete/assets propios verificados |
| Serving/cleanup | Sin commit o UNKNOWN: negar; no liberar slot/staging ni borrar ajeno | Receipt propio, custodia y binding/admisión vivos; cierre incierto conserva recursos |
| Import | Path/quota/hash/rights/DAG/propiedad/colisión inválidos: PACKAGE_INVALID/COLLISION, sin promover cierre parcial. Remap no ratificado bloquea | Intención por paquete/lote, catálogo completo y mapa autorizado D-08 |
| Backup/cut | No exclusividad o custodia UNKNOWN: bloqueo; writes/dispatch/purge suspendidos, drenar propios; no writer SQLite durante copia E/S | Coordinador maintenance propio y cut/acuses reales, no PublicationCoordinator asumido |
| Restore/activate | Corrupción/media/fk/fts/binding/rollback no conforme: conservar biblioteca/copia anterior; no activar parcial ni procesos históricos | Destino nuevo propio validado, ventana exclusiva, intención y binding/rollback D-09 |

La comprobación CAS y autoridad ocurre antes y después de los efectos que puedan dejar estado incierto. Error/close/flush desconocido no se convierte en ACK. Protocolo físico pertenece al seam liberado, no se simula en este contrato. Disco lleno/cancel/crash preservan evidencia y última copia íntegra; retry se inicia sólo tras reconciliación de identidad/custodia.

## 8. Casos válidos e inválidos por los siete sujetos

Son **casos normativos**, no fixtures ejecutados ni evidencia de producto. «Válido» significa captura y semántica de D-02: ejecución/serving siguen requiriendo el gate activo. En todos los casos, IDs/hashes son reales autorizados, tipos/límites exactos y recibos propios.

| Sujeto | Caso válido | Caso inválido / resultado |
|---|---|---|
| Asset | separate_stems captura Take T/audio H/parent+rights; required roles vocals/drums/bass/other;4assets del Take en unidad completa. mix_preview conserva MixRevision X y temporal privado sin Asset job |3roles disponibles o fuente cambió tras captura: no set parcial/retarget; PACKAGE_INVALID/SOURCE_MISMATCH. Insertar Asset.subject_type job o fingir Take para preview: PRODUCTION_INVALID |
| Analysis | analyze loudness conserva audio H/método+pin/medición; corrección timing crea revisión hija con mismos tokens/texto/audio y edits tipados | Usar beats de H1 para audio H2, reescribir fila única sin D-03 o palabra missing como cantada: SOURCE_MISMATCH/DEPENDENCY_UNAVAILABLE/INVALID; no success import por terminal engine |
| Artwork | attach_artwork_upload conserva Upload U/hash/rights+consent; Artwork source upload sin model/seed; portada Song sólo en acción CAS posterior | Foto real sin self/consented: RIGHTS_REQUIRED antes enqueue. Copiar model/seed del Take a upload o autoelegir cover: INVALID; hash PNG ajeno no autoriza |
| Render | render_n0 captura VideoProject rev7/timeline H7/audio final H/MixRevision/timing/artwork/features y perfil ratificado; receipt CPU/browser/codec real, Render propio | Editar proyecto a rev8 y renderizar H8 con request rev7, o usar features del viejo master: SOURCE_MISMATCH; no retarget. Sin reader/codec gate: DEPENDENCY_UNAVAILABLE |
| Export | export_audio target streaming congela audio/mix/letra/metadata/profile; mide salida decodificada y publica Export propio. export original conserva bytes | Inventar JobAttempt/seed para PostPlan o imponer limitador silencioso: INVALID. LUFS/peak incompatibles: NOT_CONFORMANT, no vender conforme. ZIP parcial: PACKAGE_INVALID, sin serving |
| Import | paquete cierre completo/hashes/rights/versions válido, mapa source→local explícito, staging propio; commit de todas referencias y receipt propio. Replay del mismo request devuelve mismo commit | Hash igual de archivo ajeno, ID ocupado conflictivo, path traversal, cierre incompleto o import de lease activo: COLLISION/PACKAGE_INVALID; sin adopción/promoción. Remap sin D-08: DEPENDENCY_UNAVAILABLE |
| Backup | backup_library congela corte exclusivo SQLite+media; restore valida biblioteca nueva ext4, jobs inertes; activate usa binding raíz/BD y rollback propios | Backup sólo BD vendido como biblioteca, VHDX activo copiado, custodia UNKNOWN o activar destino parcial: INVALID/CUSTODY_UNKNOWN/PACKAGE_INVALID; conserva biblioteca/copia íntegra anterior |

Adicionales comunes: bool como version1, extras de otra rama, UTF-8 BOM, JSON duplicado, >2MiBrequest/>1MiBrecipe, >64sources/parents/roles, >16profiles o profile>64KiB,65lyricsversions o texto32769chars, path1025chars y overflow revision rechazan antes enqueue. Pasar límite de caracteres no implica pasar bytes agregados. Unknown reader/version rechaza sin fallback; los lectores legacy despachan histórico sin reescritura.

## 9. CA-02, CA-44, CA-48 y contratos posteriores

| CA | Concreción que cierra D-02 | Evidencia real aún pendiente |
|---|---|---|
| CA-02 / E2E-02 | Request/recipe write-once; IDs/hashes/revs/padres/letra/rights/perfiles efectivos; cambio de maestro/letra/preset no retargetea; rev/CAS de publicación aparte | T12/T14 e integración: comparar bytes/hashes before/after y autoridad real; sin prueba musical ficticia |
| CA-44 / E2E-44 | Intención preefecto por unidad, terminales distintos, committed gana, replay propio sin regenerar, cancel/crash por fronteras; UNKNOWN bloquea efectos/serving/cleanup/slot | Raw/post/rename/commit/render/import/backup reales, restart/cancel/acuse perdido, ext4/custodia y lector final; no alcanzado por prosa |
| CA-48 / M-48 | Executor real por sujeto; procedencia/pins/hashes/rights, AND commercial_use; familias/versiones separadas; historical v1/v2 sin rewrite, CPU sin inferencia dummy; DTO M1 compatible | Code-first/code-schema/OpenAPI coordinados, reader/emisor/migración real y acta independiente; no porcentajes o aceptación inventados |

D-03 debe cerrar datos/revisiones/constraints para intentos/resultados multi-sujeto, Analysis y mixed origins antes T13/T16/T20/T29. Baseline23tablas inmutable, nuevas migraciones aditivas; excepción ADR-0074 sólo sus tres tablas. D-04 debe cerrar formatos por sujeto: inferencia histórica manifest1; CPU Take autónomo/previews y song con cierre CPU version2 según ADR-0074; un resultado M3 que no encaje exige formato discriminado y decisión previa, no relajación silent de v1/v2. TimelineV1 cerrado no recibe palabras/bindings extras. Readers futuros despachan family+version y rechazan desconocida; conservan bytes originales/padres/rights.

D-05–09 deben ratificar perfiles/readers/planes/catálogos/quota/remap y binding/cut/activation antes RED de sus ramas. Hasta entonces, refs tipadas son requisitos de captura y la rama devuelve DEPENDENCY_UNAVAILABLE; no hay catch-all para ejecutar. Esta dependencia no deja abiertos discriminantes/versiones/límites/owner/terminal/CAS de D-02 ya definidos. D-11 y capacidades de análisis/engine tienen gates reales independientes. Las ocho operaciones CreativeRequestV1 siguen intactas; mezcla publicada como Take hijo usa CPU/M2 con todos sus antecedentes, no Export convertido en inferencia.

## 10. Fuentes SHA, alcance de escritura y entrega

| Fuente del corte ROOT | SHA-256 |
|---|---|
| `apps/server/app/worker/contracts.py` | `4c04a5a5698e88ab1d31f65e9f3924e6b63e077b6dc2ee282f35da2c85fb891b` |
| `apps/server/app/worker/planning.py` | `3aca3783d91b398fc4932f0c61759563cc2a1d4088ce23ef81b0186148bb8dcd` |
| `apps/server/app/worker/publications.py` | `c905685a2b5b7ac689578707e548440f3939ddbf22e6fb71bf77ec4128fae054` |
| `apps/server/app/models/__init__.py` | `9c86ef171968e799908068c1f98ce47186b9e2ed3337c019a7e9696d38dac0df` |
| `apps/server/app/creative/recipes.py` | `d8eb051277b436f5ba049611221a1bfc9161e1a5561dd984058ce76d645ab9ca` |
| `packages/audio-post/audio_post/private_context.py` | `0397c05c53785f9068daef896ef92fb3a3c9a2ed6772dfb7f790ac9ad6c65c23` |
| `docs/arquitectura/contrato-engines.md` (prefijo histórico) | `122e0eeb3f18bf2c7d7b967ee02462b090c7a230ecb02b8a2fdb0fde5e9bd471` |
| `docs/arquitectura/datos.md` (prefijo histórico) | `a5ffb07c5de4e8598162e91338868f14772ca0fdcd82ebb13c23dbcc4f2f3547` |
| `docs/decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md` | `e57e656253e7829ba2122996112a2517ac08c153f4c1ad1a150d182f59aab8e4` |
| `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md` | `3197ba5865de09733dcd66f0f320b162f3d00dbe3aa5e7da2aca78ea91dc9633` |

El recibo release-root conserva el inventario completo78fuentes; elección ROOT ratifica19parejas, límites y representación privada. Esos SHA identifican el corte, no disponibilidad runtime. Se conservan76pins nonowned y options históricos inmutables. Sólo se redactan este contrato y apéndices al final de los dos documentos owned del snapshot; prefijos históricos byteexactos. ADR sin número es candidato privado para revisión/adopción ROOT, no nueva decisión canónica unilateral.

TDD n/a: prosa documental. La verificación de lectura exige casos válidos/invalidos por7sujetos y elección ROOT trazada; guards, SHA, diff exacto, links desde destino canónico y manifest de entrega se conservan en namespace privado. No se ejecutan E2E/GPU/native/ext4, no hay implementación/migración/instalación, no se actualiza ledger/Git/canon/medidor y no se declara T-02 cerrada. ROOT ordena revisión A/B y QA independientes; aceptación final y adopción permanecen pendientes.


## Acta ROOT de ratificación D-02 y adopción T-02 — 2026-10-11T19:03:55.596469+00:00

ROOT ratifica PR-O1 y el contrato campo/tipo/versión/owner/terminal/CAS/fallos,19parejas y7sujetos con casos válidos/inválidos. Elección completa previamente registrada bajo delegación del usuario; ninguna revisión personal del propietario se atribuye. Revisión fresca A/B sin gaps y QA independiente403/403 controles documentales/qa-gate0. ADR-0082 adoptada y apéndices correspondientes incorporados. Las referencias anteriores a borrador, T02 abierta, candidato sin numerar o review/QA/adopción pendientes describen el corte preadopción y quedan supersedidas por esta acta para el estado documental.

T02 cierra sólo concreción; CA02/44/48 tienen definición, no aceptación del comportamiento. M1formal0/17, M2=4/30, M3=2/42documentales yfuncionesM3=0. D03SQL/D04formats/D05–09perfiles/catálogo/biblioteca y sus gates permanecen pendientes antesREDdependiente. Snapshot81/79guards corresponden al sellodeQA anterior aK1append; ROOTdeclaraese cambio postfreeze, no atribuye preimages viejas al estado nuevo. Casos normativos no son tests de producto;34E2E/15manuales siguen pendientes. Sin inferencia ficticia, grant/roottrust porhash o artefacto, ni garantías de storage/render/import/backup por prosa. RuntimeAPI/ORM/DDL/M1DTO/enginev1/readers históricos intactos. Uso realnull.
