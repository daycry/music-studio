---
design: m3-production-data-d03
titulo: Persistencia aditiva de producción y revisiones inmutables
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: ../2026-10-11-m3-produccion-portada-video-letra/spec.md
evaluacion: n/a
plan: ../2026-10-11-m3-produccion-portada-video-letra/improvement-plan.md
adr: candidato sin número; reserva y adopción ROOT pendientes
opcion_elegida: PD-O1
adopcion: propuesta seleccionada; pendiente revisión, QA y adopción ROOT
validacion: ROOT bajo delegación vigente; 2026-10-11T19:28:24.366015+00:00
recomendada: PD-O1
decision: D-03
namespace: candidato privado del snapshot; no canon ni autoridad runtime
model_tier:
  agente: architect
  model: opus
  effort: high
  fuente: frontmatter del recibo ROOT; no afirma modelo ejecutado
generacion:
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  nota: Sin estimación numérica; marcador exclusivamente ROOT.
---

# Diseño D-03 — persistencia de producción y revisiones

| Campo | Valor |
|---|---|
| Estado | Arquitectura elegida; fuente propuesta seleccionada pendiente revisión/QA/adopción ROOT |
| Opción elegida | PD-O1 |
| Validación | ROOT bajo delegación vigente, 2026-10-11T19:28:24.366015+00:00 |
| TDD | n/a: comparación arquitectónica y prosa, sin implementación |
| Alcance | T-03 documental; funciones M3 implementadas: 0 |

## 1. Contexto y restricciones

T-03 concreta CA-02/08/18/20/34/48 antes del RED dependiente. La spec de M3 está aprobada. ROOT acredita T-01/T-02 documentales cerradas: M3 2/42, M2 4/30 y M1 formal 0/17. K1 está aceptado como componente; ningún hito completo está aceptado.

El snapshot privado contiene 99 fuentes verificadas contra `release-root.receipt.json`, con cero diferencias SHA. Las fuentes se leen sin importar aplicaciones, abrir SQLite ni ejecutar Alembic. Sólo este `design.md` pertenece al actor. ROOT conserva ledger, métricas, canon, Git y adopción.

### Hechos del corte code-first

| Fuente real | Hecho comprobado |
|---|---|
| `apps/server/app/models/__init__.py:235` | `Analysis` posee `take_id`, `kind`, `analyzer_id`, `analyzer_version`, `lyrics_version_id` y `data`; UNIQUE exacto `(take_id,kind,analyzer_id)` |
| `apps/server/app/models/__init__.py:197` | `Asset.subject_type` admite `take artwork shot_version render export character lora cli_run`; excluye `job analysis import backup` |
| `apps/server/app/models/__init__.py:297` | Preset global: `kind`, `name`, `payload`; no historia revisionada propia actualmente |
| `apps/server/app/models/__init__.py:556` | `PublicationIntent` existente pertenece a Take; no representa todos los sujetos M3 |
| `apps/server/app/models/__init__.py:570` | Revisión M1 exige contexto Take/ganador y paquete propio; no se reutiliza con inferencia ficticia |
| `apps/server/app/db.py` | Server usa SQLite, WAL, `foreign_keys=ON`, timeout 5000 ms y transacciones explícitas; snapshots son proyección posterior al commit |
| `apps/server/app/migrations/versions/0007_job_attempt_json_guard.py` | Head del inventario es `0007`, hijo de `0006`; cualquier evolución parte de ese head verificado |
| `apps/server/app/migrations/initial_invariants.py` y `fix1_invariants.py` | Pertenencia, DAG y raíz canónica se verifican mediante triggers; raíz Take deriva del mínimo de raíces originales alcanzables |
| `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-request-contract.md` | D-02 ratificada:19parejas,7sujetos, límites, capturas privadas, recibos discriminados y CAS por resultado |

No se inventa un UNIQUE `(take,method)` diferente: el método contractual se representa por `kind` y el analyzer real. `analyzer_version` no forma parte del UNIQUE histórico. Tampoco se presenta `OriginalAnalysis` como tabla existente: designa la evidencia inicial preservada.

### Restricciones comunes a las opciones

Constitución §1/§2 obliga a conservar Song como proyecto, Take inmutable, server como escritor único y engines raw. No hay sesión agregada persistente, runner paralelo ni infraestructura nueva. La cola sigue siendo `job/job_dependency`.

ADR-0074 permite reconstrucción/relajación únicamente de `take`, `publication_intent` y `publication_intent_revision` para sus ausencias CPU delimitadas. D-03 añade tablas y guards; no amplía esa excepción a Analysis, Asset o Preset. Las migraciones históricas permanecen intactas.

ADR-0077/0079 conserva recetas y planes M2 sellados. Sus validadores puros acreditan coherencia del componente, no archivos, inferencia, integración M1/T-02 ni autoridad runtime. La captura M3 no importa codecs privados M1 ni convierte historia a un formato nuevo.

ADR-0080/0082 exige resultados tipados independientes: Asset/set, Analysis, Artwork, Render, Export, import y backup. Import reserva destino propio sin Song ficticia existente. Backup usa scope de biblioteca sin Take/Song ficticios. Preview temporal permanece privado del job.

D-04 fija formatos de publicación; D-05–09 fija perfiles y capacidades específicas. D-03 cierra estructura, identidad y validación relacional. No sustituye esos gates con un dict libre. Los readers nuevos rechazan versión desconocida y no completan históricos con defaults.

## 2. Opciones (2)

### PD-O1 — Tablas tipadas y relaciones normalizadas con capturas propias

Añadir familias SQL distintas para mix, análisis por método, timing, preset e intención/revisión/recibo de producción. Claves relacionales gobiernan pertenencia, revisiones, resultados y bindings. Las capturas canónicas privadas conservan evidencia original y derechos referenciados.

MixRevision usa filas hijas para cada stem y sus controles. LyricsTimingRevision usa bindings históricos y tokens/segmentos revisionados. PresetRevision congela nombre, clase, valores y refs efectivos. Ninguna edición actualiza una revisión previa.

Analysis conserva su fila original y UNIQUE histórico. Un resultado M3 nuevo vive en una tabla adicional de resultados por método, con ID/result_key y versiones propias. Un enlace opcional a Analysis identifica evidencia legacy; no simula un analyzer nuevo para esquivar el UNIQUE.

ProductionIntent incorpora discriminadores Song/biblioteca y resultado, clave reservada, CAS y cursor activo. ProductionIntentRevision y ProductionReceipt conservan fases y terminales propios. Tablas de refs tipadas conectan cada resultado a su entidad real; import/backup permanecen operaciones privadas.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: más tablas y triggers para relaciones directas y comprobaciones inversas |
| Riesgo | Medio: olvidar una guarda inversa o confundir la revisión CAS con una revisión de contenido |
| Coste relativo | L: más DDL y fixtures de migración; menor dependencia de funciones JSON para relaciones |
| Reversibilidad | Alta antes de datos M3; después exige dejar historia intacta y deshabilitar uso, sin DROP destructivo |

### PD-O2 — Documentos tipados versionados con índices relacionales y lectores SQL

Añadir registros independientes por familia, cada uno con bytes canónicos cerrados, SHA y columnas de identidad/owner/scope/padre/revisión. Los campos de mix, timing y preset se conservan en documentos versionados completos. Las refs a entidades y resultados mantienen índices/FK relacionales propios.

ProductionIntent conserva cursor CAS relacional; revisiones y recibos son documentos inmutables por fase. Triggers SQL invocan lectores cerrados registrados en todas las conexiones, siguiendo el patrón actual de validación durable. La ausencia del lector falla cerrada.

Analysis legacy sigue intacta. Los documentos de resultado por método se añaden fuera de su UNIQUE y se leen mediante despacho explícito. Los documentos de timing identifican resultado inicial, binding de letra/audio y padre; no modifican `Analysis.data`.

Esta opción no es un agregado de sesión ni un JSON de parámetros arbitrarios. Cada familia posee reader/version/schema propios y refs indexadas. Los readers validan también los negativos por SQL directo; una lectura ORM aislada no basta.

| Criterio | Valoración |
|---|---|
| Complejidad | Media en DDL; alta en lectores cerrados y registro de validadores por conexión |
| Riesgo | Medio-alto: duplicar claves dentro/fuera del documento o perder validación en conexiones de migración/import |
| Coste relativo | M: menos tablas de contenido, mayor superficie de codecs y validadores |
| Reversibilidad | Alta antes de datos M3; después exige conservar bytes y readers legacy, sin borrar documentos |

### Obligaciones comunes cerradas por el contrato seleccionado de §4

| Área | Invariante normativa de la segunda pasada |
|---|---|
| Identidad | ULID, owner y scope exactos; request/job/recipe/SHA/result_key congelados; refs de entidad y comprobaciones inversas |
| Single/composite | Single tiene una letra histórica; composite conserva versiones y bindings medidos propios, sin LyricsVersion sintética |
| Duración | Audio efectivo identificado por ID/SHA y medición de frames/rate; timing ligado a esa duración, sin truncación180s |
| Mix | Set4roles exacto; stem ID/hash/rate/frames/canales; mute domina solo; solos seleccionan sólo no muteados; ganancia finita; bytes originales intactos |
| Timing | Resultado inicial preservado; padre y tokens estables, tiempos/uncertainty/missing/instrumental y origen de corrección propios |
| Preset | Historia immutable, refs efectivas congeladas; edición o borrado no retargetea request/render anterior |
| Grafo | Padres reales, owner/canción común cuando aplica, DAG y raíces originales; biblioteca/preset global no adquiere root Take ficticia |
| Capturas | SourceSnapshot privado inmutable y refs cerradas de rights/perfiles; SHA identifica bytes, nunca concede derechos/admisión |
| Reservas | Intención y fase reserved durables antes de efectos; evidencia de reserva distingue hechos previstos de resultados ejecutados |
| Evidencia | `result_evidence_ref` obligatorio de cada revisión apunta a evidencia existente de su fase; sólo una fase posterior puede referir resultado ejecutado |
| CAS | Compara estado/revisión/cursor activo e identidad completa; incrementos estrictos y sin overflow; resultado committed inmutable |
| Recibos | engine_raw/cpu_result/upload_result/publication/import/maintenance independientes; execution no fabrica JobAttempt ni terminal ganador |
| Publicación | Entidad real, set completo y receipt final juntos en commit SQLite; rename tiene recovery propio, no atomicidad conjunta inventada |
| Privacidad | Capturas/rights privadas; DTO/log/portable no transportan secretos, paths personales ni autoridad viva |

La reserva puede portar una evidencia privada `reserved`, existente y ligada al request; nunca porta ProductionReceipt succeeded ni un resultado imaginado. Ejecutar obtiene evidencia nueva. El cambio de fase crea una revisión nueva y mueve el cursor mediante CAS. Este cierre evita exigir evidencia de ejecución antes de ejecutar sin hacer nullable por conveniencia el campo D-02.

## 3. Criterios de decisión

1. Preservar byte a byte Analysis, manifiestos/recetas/planes y contratos históricos, incluida la excepción ADR-0074 delimitada.
2. Rechazar por SQL directo claves, pertenencia, fases y relaciones inválidas; garantizar también referencias inversas y lectores legacy.
3. Separar reserva previa, ejecución real, preparación y commit; una revisión inmutable no evoluciona por overwrite.
4. Compartir CAS y recibos entre sujetos sin Take, analyzer, JobAttempt ni sesión agregada ficticios.
5. Fijar single/composite y duración del audio efectivo, distinguiendo plan puro de evidencia medida runtime.
6. Evitar doble autoridad entre documento y columnas; mantener rollback sin pérdida de datos ni reactivación de jobs.

## 4. Recomendación · opción elegida y por qué

**Recomendación del arquitecto: PD-O1.** Las tablas tipadas permiten comprobar bindings, pertenencia y resultados mediante relaciones explícitas. Reducen la dependencia de codecs de documentos para integridad referencial. Su coste DDL mayor responde a los criterios2/3/5.

**Opción elegida: PD-O1.** ROOT la elige bajo delegación vigente del usuario, con recibo `choice-root.receipt.json` SHA `c0c651cee5b4a0eaa58fa02ac3a9a081a6dad49cfe3dbd6cd6a44b7e54495ea1`. La primera pasada completa queda preservada en `options-preserved-root.md`, SHA `428b5cecdbde017ce5616a7c139e4cec6a81674e177e58011398deb668a91cd4`. Se comprobaron ambos archivos antes de esta segunda pasada.

PD-O1 responde a criterios2/3/5 con FK y comprobaciones inversas explícitas y preserva criterios1/4/6 sin documento de sesión. PD-O2 se descarta por mayor dependencia de codecs registrados y doble proyección de identidad; sigue siendo técnicamente viable. `estado: aprobado` usa el vocabulario propio del diseño y registra sólo la elección arquitectónica. La **fuente propuesta seleccionada** no está adoptada en canon, no cierra T-03, no prueba producto y permanece pendiente de revisión/QA/adopción ROOT.

### Decisión ADR pendiente

La elección cruza el umbral: afecta datos, cola, publicación, lectores y recovery. §7 incluye texto ADR candidato sin número. ROOT reservará y adoptará el ADR después de revisión/QA. No se crea ADR público ni se modifica un índice en esta pasada.

### 4.1 Alcance normativo y notación DDL

Lo siguiente es especificación de DDL/readers futuros, **no SQL ejecutado ni código implementado**. Todos los nombres nuevos llevan `m3_`; no se sustituyen tablas baseline. No se crea `OriginalAnalysis`: el término significa la fila Analysis original. La raíz de migración es `down_revision="0007"`; ROOT/implementador reservará un revision ID nuevo al implementar, sin renumerar historial.

Cada lista de columnas es exhaustiva. `?` significa SQL NULL permitido; las demás son NOT NULL. No hay defaults implícitos nuevos ni columnas `updated_at/deleted_at` ocultas. `H` expande exactamente a `id U PRIMARY KEY, owner_id U REFERENCES user(id), created_at UTC`. `U=TEXT` con `typeof='text'`, longitud26, primer carácter0..7 y alfabeto ULID histórico; `S=TEXT`64hex minúsculos; `R=INTEGER` con `typeof='integer' AND 1<=x<=9223372036854775807`; `N=INTEGER` con mismo tipo y0..MAX; `B=INTEGER` con tipo entero y `IN(0,1)`; `F=REAL` con `typeof='real'`, no NULL, finito mediante `abs(x)<=1.7976931348623157e308`; `UTC=TEXT` ISO8601 UTC aceptada por reader estricto, sufijoZ; `L=TEXT`1..512caracteres Unicode; `P=TEXT` path POSIX relativo1..1024 confinado y validado por reader; `J=BLOB` bytes canónicos UTF-8 JSON sin BOM, extras ni duplicados. Una columna nullable aplica sus checks sólo si no es NULL. No se usa afinidad SQL para autorizar coerción en DTO: reader estricto antes del binding SQL; SQL verifica el tipo almacenado.

Cada FK indicada, simple o compuesta, es `DEFERRABLE INITIALLY DEFERRED ON UPDATE NO ACTION ON DELETE NO ACTION`. **No** CASCADE, SET NULL ni REPLACE. Todas las columnas FK simples tienen índice `ix_<table>_<column>`; toda FK compuesta tiene índice `ix_<table>_<columns_en_orden>` salvo prefijo idéntico de PK/UNIQUE ya cubierto. Cada UNIQUE se declara como constraint completo, no depende de índices parciales ni de valores NULL no comparables. Cada enum de esta sección es CHECK exacto. No se agregan valores a Asset/Analysis/Take/Export/timeline-v1 ni al DTO M1.

`G-xx` identifica un trigger normativo: la tabla §4.12 fija momento, columnas, predicado y acción. El DDL futuro debe expandirlos con nombres `m3_g<xx>_<table>_<insert|update|delete>` sin modificar guards existentes. Todos abortan con `RAISE(ABORT,...)` ante falso; no autocorrigen filas. Guards se ejecutan también con SQL directo, no sólo por ORM.

### 4.2 Scopes, capturas privadas y fuentes

| Tabla | Columnas exactas | PK/UNIQUE y checks adicionales |
|---|---|---|
| `m3_scope` | H; `kind TEXT`; `scope_key U`; `song_id U? -> song.id`; `binding_reader L?`; `binding_version R?`; `binding_sha256 S?`; `binding_payload J?` | UNIQUE(owner_id,kind,scope_key). kind song/library. Song: binding cuatro campos NULL, song_id NULL o igual scope_key; library: song_id NULL y cuatro binding campos NOT NULL. Library scope_key=binding_id exacto del BindingRef ratificado; byte/hash/reader coinciden. Song NULL sólo reserva de destino import, nunca canción ficticia |
| `m3_capture` | H; `scope_id U? -> m3_scope.id`; `family TEXT`; `reader L`; `version R`; `payload J`; `sha256 S`; `bytes N` | bytes=length(payload), hash exacto; family enum request/recipe/profile/measurement/revision/catalog/closure/binding/execution/publication/historic/rights/reservation/phase. No UNIQUE por hash: bytes iguales no comparten autoridad |
| `m3_capture_dependency` | `capture_id U -> m3_capture.id`; `ordinal N`; `dependency_id U -> m3_capture.id`; `role L` | PK(capture_id,ordinal); UNIQUE(capture_id,dependency_id,role); capture_id!=dependency_id. Orden contiguo0..count−1; DAG comprobado G03; owner compatible; global sólo consumido por su owner |
| `m3_source_snapshot` | H; `scope_id U? -> m3_scope.id`; `kind TEXT`; `source_id U`; `role L`; `sha256 S`; `media_type L`; `bytes N`; `evidence_capture_id U -> m3_capture.id`; `asset_id U? -> asset.id`; `upload_id U? -> upload.id`; `analysis_id U? -> analysis.id`; `analysis_result_id U? -> m3_analysis_result.id`; `artwork_id U? -> artwork.id`; `render_id U? -> render.id`; `export_id U? -> export.id`; `package_capture_id U? -> m3_capture.id` | kind asset/upload/analysis/artwork/render/export/package. EXACTAMENTE un destino: analysis admite analysis_id XOR analysis_result_id; package sólo package_capture_id. source_id igual ID del destino excepto package: ID propio del catálogo/package capturado, validado por reader de paquete. Roles/bytes/hash/evidence exactos. No slot job/import/backup |
| `m3_rights_snapshot` | H; `scope_id U? -> m3_scope.id`; `ref_kind TEXT`; `entity_kind TEXT?`; `entity_id U?`; `pin_id L?`; `kind TEXT`; `declaration TEXT`; `real_person B`; `consent TEXT`; `commercial_use B`; `sha256 S`; `evidence_capture_id U -> m3_capture.id` | ref_kind entity/pin; entity→entity_kind+entity_id NOT NULL,pin NULL; pin inverso. entity_kind asset/upload/analysis/artwork/render/export/package/take/lyrics_version; kind audio/image/lyrics/parent/tool/model; declaration own/assistant/licensed/consented/public_domain; consent self/consented/n_a. Assistant sólo lyrics; consented sólo audio/image; tool/model→pin,licensed,false,n_a. Foto real→self/consented. Polimorfismo cerrado G04, no entidad inventada |

Capturas no conceden autoridad runtime. `m3_capture` almacena evidencia original y cierra dependencias; sus rows y dependencies son append-only. Los readers de historic conservan bytes v1/v2 originales, sin recanonicalizar, añadir defaults ni límites nuevos retroactivos. Los J nuevos sí usan canónico D-02. Request≤2097152bytes, recipe≤1048576; profundidad≤32; sources/parents/roles≤64, profiles≤16 y cada profile≤65536bytes, lyrics versions≤64, cada texto≤32768caracteres. Cualquier límite de paquete/media pertenece al reader D-08/09 y bloquea consumo hasta ratificado; D-03 no impone cuota musical ni truncación180s.

G02 valida captura con despacho cerrado; G04 valida cada destino de fuente/rights y su owner/scope transitivo. Sources pueden tener scope global NULL sólo para uploads/biblioteca permitidos; un asset de Take no se convierte en global. `m3_scope.song_id` se materializa NULL→scope_key **únicamente** dentro del commit import completo y con Song real del mismo owner; no permite cambiar scope_key. Los efectos previos de import se vinculan a la reserva scope_id propia; `job.song_id` permanece NULL hasta materialización, sin FK diferida a Song ausente al reservar. Después se enlaza job/song en ese mismo commit si su estado/guards baseline lo permiten; no exige asignar Song ficticia al crear job.

Una fila referenciada no se borra físicamente. Soft-delete de Song/Upload puede revocar acceso nuevo sin borrar snapshots: autenticación/rights actuales bloquean nuevo efecto/serving donde corresponda. G13 protege identidad, media y pertenencia; no congela el nombre/payload actual de Preset ni las selecciones actuales de Song. SHA atestigua bytes, no copyright, consentimiento, permiso ni custodia.

### 4.3 Letra histórica y audio efectivo

| Tabla | Columnas exactas | PK/UNIQUE y checks adicionales |
|---|---|---|
| `m3_lyrics_context` | H; `scope_id U -> m3_scope.id`; `take_id U -> take.id`; `kind TEXT`; `origin_capture_id U -> m3_capture.id` | kind none/single/composite; scope Song existente del Take. Original single tiene exactamente1member,0bindings; none0/0; composite1..64members y>=1binding real |
| `m3_lyrics_member` | `context_id U -> m3_lyrics_context.id`; `ordinal N`; `lyrics_version_id U -> lyrics_version.id`; `sha256 S`; `text TEXT`; `declaration TEXT` | PK(context_id,ordinal); UNIQUE(context_id,lyrics_version_id); orden contiguo; texto0..32768Unicode y hash del UTF-8 exacto; declaration own/assistant/public_domain/licensed; mismo Song/owner |
| `m3_lyrics_binding` | H; `context_id U -> m3_lyrics_context.id`; `ordinal N`; `lyrics_ordinal N`; `parent_take_id U -> take.id`; `parent_audio_sha256 S`; `parent_start_frame N`; `parent_stop_frame N`; `destination_start_frame N`; `destination_stop_frame N`; `parent_sample_rate R`; `destination_sample_rate R`; `mapping_capture_id U -> m3_capture.id`; `measurement_capture_id U -> m3_capture.id` | FK(context_id,lyrics_ordinal)→m3_lyrics_member(context_id,ordinal); UNIQUE(context_id,ordinal). start<stop en ambos ejes; rates<=2147483647. Map/cuentas medidos; sin asumir longitudes iguales al convertir. Fragmentos pueden solapar sólo si mapa real mezcla y conserva ambos antecedentes |
| `m3_audio_binding` | H; `scope_id U -> m3_scope.id`; `take_id U -> take.id`; `kind TEXT`; `asset_id U? -> asset.id`; `mix_revision_id U? -> m3_mix_revision.id`; `audio_sha256 S`; `sample_rate R`; `channels R`; `frames R`; `duration_s F`; `measurement_capture_id U -> m3_capture.id`; `execution_receipt_id U? -> m3_receipt.id`; `media_capture_id U -> m3_capture.id` | kind master/mix; master→asset NOT NULL,mix NULL; mix inverso y execution_receipt NOT NULL cpu_result succeeded. sample_rate<=2147483647; channels1/2; duration_s>0 y exactamente float(frames/sample_rate) del reader; hash/rate/channels/frames medidos sobre bytes efectivos |

Contexts no se derivan de `Song.current_lyrics_version_id`. El single se captura del Take/historia real; composite conserva versiones históricas y bindings medidos, sin crear LyricsVersion sintética ni concatenar texto como autoridad. Si historia no acredita contexto, se conserva leíble y se rechaza operación nueva que necesita letra. Un mapa M2 puro basta para describir plan, pero no `measurement_capture_id` ni resultado medido: caller mide audio final y valida spans/rates/hash/frame count. Mismatch falla sin modificar plan ya sellado.

Audio mix no implica Asset.subject_type mix/job. `media_capture_id` refiere inventario privado de un CPU result real y ruta de staging propia acreditada; hasta publicar, no hay asset durable servido. `audio_binding` describe bytes reales de esa ejecución, no una suma hipotética. El master preserva los bytes originales y Take. Lyrics context puede conservar composite histórico incluso en mix; timing está unido al audio_binding **exacto**, no a Take/master mutable. Revisión de mix antes de preview no requiere inventar audio_binding de salida: se liga al binding de entrada del stem set; sólo ejecutar crea binding mix medido.

### 4.4 Stems y MixRevision

| Tabla | Columnas exactas | PK/UNIQUE y checks adicionales |
|---|---|---|
| `m3_stem_set` | H; `scope_id U -> m3_scope.id`; `take_id U -> take.id`; `input_audio_binding_id U -> m3_audio_binding.id`; `result_key U`; `execution_receipt_id U -> m3_receipt.id` | UNIQUE(scope_id,result_key); receipt engine_raw o cpu_result succeeded propio de separate_stems; input mismo Take; miembro set sellado=4roles exactos |
| `m3_stem_member` | `set_id U -> m3_stem_set.id`; `role TEXT`; `engine_role L`; `asset_id U -> asset.id`; `sha256 S`; `sample_rate R`; `channels R`; `frames R`; `offset_frames N`; `measurement_capture_id U -> m3_capture.id` | PK(set_id,role); UNIQUE(set_id,asset_id); role vocals/drums/bass/other; asset.subject_type take y subject_id set.take_id,asset.role='stem:'||role; rates/channels/frames iguales entre4,offset_frames=0; rate<=2147483647,channels1/2; hashes reales |
| `m3_mix_revision` | H; `scope_id U -> m3_scope.id`; `take_id U -> take.id`; `set_id U -> m3_stem_set.id`; `lineage_id U`; `revision R`; `parent_revision_id U? -> m3_mix_revision.id`; `origin TEXT` | UNIQUE(lineage_id,revision); origin initial/user/import. revision1→parent NULL y lineage_id=id; otra→padre misma lineage/scope/take/set,revision=padre+1. No reset/overflow; import no afirma autoría local |
| `m3_mix_stem` | `mix_revision_id U -> m3_mix_revision.id`; `role TEXT`; `mute B`; `solo B`; `gain_linear F` | PK(mix_revision_id,role); role4enum, gain_linear>=0, finito; exactamente4controles que coinciden con set sellado |
| `m3_mix_head` | `lineage_id U PRIMARY KEY -> m3_mix_revision.id`; `owner_id U -> user.id`; `revision R`; `active_revision_id U -> m3_mix_revision.id` | UNIQUE(active_revision_id). Head sólo revisión sellada de la lineage; cambio CAS compara ambos campos actuales y apunta a revision+1,parent=OLD.active |

Ganancia persistida es lineal y adimensional, no dB ambiguo. Ningún límite de amplitud adicional se inventa; F finito y>=0, y suma no finita/clipping se trata por perfil/evidencia D-05, no por normalización implícita. `any_solo=OR(solo_i)` sobre los4controles, incluso si un solo está muteado. `effective_gain_i=0` si mute_i OR (any_solo AND NOT solo_i), si no gain_linear_i. Todos muteados, todas ganancias0 o únicos solos muteados producen silencio. Varios solos no muteados se suman; mute siempre prevalece. Preview/export consumen ID/hash de revisión sellada, nunca head implícito. Reload reconstruye los mismos4valores y bytes de stems/master permanecen idénticos. Un edit crea nueva revisión completa; head mutable es selección CAS, no revisión mutable.

### 4.5 Resultados Analysis y revisión LyricsTiming

| Tabla | Columnas exactas | PK/UNIQUE y checks adicionales |
|---|---|---|
| `m3_analysis_result` | H; `scope_id U -> m3_scope.id`; `take_id U -> take.id`; `audio_binding_id U -> m3_audio_binding.id`; `result_key U`; `method TEXT`; `analyzer_id L`; `analyzer_version L`; `origin TEXT`; `outcome TEXT`; `lyrics_context_id U? -> m3_lyrics_context.id`; `legacy_analysis_id U? -> analysis.id`; `data_capture_id U? -> m3_capture.id`; `execution_receipt_id U? -> m3_receipt.id`; `error_code L?` | UNIQUE(scope_id,result_key); method beats/sections/key/loudness/lyrics_timing; origin engine/cpu/legacy/import/textual; outcome succeeded/failed/missing. succeeded→data NOT NULL,error NULL; failed/missing→data NULL,error NOT NULL. lyrics_timing→context NOT NULL; demás context NULL. Legacy exige legacy_analysis_id y historic evidence; nuevo engine/cpu exige receipt real correspondiente; textual sólo sections y evidencia textual explícita |
| `m3_analysis_head` | `owner_id U -> user.id`; `scope_id U -> m3_scope.id`; `take_id U -> take.id`; `audio_binding_id U -> m3_audio_binding.id`; `method TEXT`; `analyzer_id L`; `revision R`; `active_result_id U -> m3_analysis_result.id` | PK(take_id,audio_binding_id,method,analyzer_id); método exacto anterior; head mantiene owner/scope/audio/method/analyzer, sólo result sellado; revision inicial1,incremento CAS+1. analyzer_version no se añade a UNIQUE baseline |
| `m3_timing_revision` | H; `scope_id U -> m3_scope.id`; `take_id U -> take.id`; `initial_result_id U -> m3_analysis_result.id`; `audio_binding_id U -> m3_audio_binding.id`; `lyrics_context_id U -> m3_lyrics_context.id`; `lineage_id U`; `revision R`; `parent_revision_id U? -> m3_timing_revision.id`; `origin TEXT`; `execution_receipt_id U -> m3_receipt.id` | UNIQUE(lineage_id,revision); origin alignment/user/import. Primera→revision1,lineage=id,parent NULL,origin alignment o import; hija→padre+1 misma lineage/initial_result/audio/context/take; user requiere cpu_result propio correct_lyrics_timing. Initial result sellado method lyrics_timing succeeded. Import receipt propio con procedencia original, no terminal engine local inventado |
| `m3_timing_line` | `revision_id U -> m3_timing_revision.id`; `line_id U`; `ordinal N`; `lyrics_ordinal N`; `binding_id U? -> m3_lyrics_binding.id`; `char_start N`; `char_stop N`; `text TEXT`; `state TEXT`; `start_s F?`; `end_s F?`; `confidence F?` | PK(revision_id,line_id); UNIQUE(revision_id,ordinal). estado aligned/uncertain/missing; char_start<char_stop; texto exacto slice Unicode histórico, no trim/normalización; aligned/uncertain→0<=start<end<=duration,missing→ambosNULL; confidence NULL o0..1. Reader comprueba member dentro context; binding obligatorio composite,NULL single |
| `m3_timing_word` | `revision_id U`; `token_id U`; `line_id U`; `ordinal N`; `char_start N`; `char_stop N`; `text TEXT`; `state TEXT`; `start_s F?`; `end_s F?`; `confidence F?` | FK(revision_id,line_id)→m3_timing_line(revision_id,line_id); PK(revision_id,token_id); UNIQUE(revision_id,line_id,ordinal). mismos checks estados/tiempos; caracteres dentro line slice, texto exacto; palabra timed dentro línea timed; missing no es palabra cantada |
| `m3_timing_region` | `revision_id U -> m3_timing_revision.id`; `ordinal N`; `kind TEXT`; `start_s F`; `end_s F`; `evidence_capture_id U -> m3_capture.id` | PK(revision_id,ordinal); kind instrumental/uncertain;0<=start<end<=duration. Instrumental no solapa intervalo de palabra aligned; uncertain puede solapar palabra incierta y no equivale a certeza |
| `m3_timing_head` | `lineage_id U PRIMARY KEY -> m3_timing_revision.id`; `owner_id U -> user.id`; `revision R`; `active_revision_id U -> m3_timing_revision.id` | UNIQUE(active_revision_id); mismo CAS de mix head; sólo revisión sellada |

FK de `m3_timing_line` a miembro se resuelve con CHECK de G08 porque context_id reside en root; no se duplica como columna mutable. SQL trigger comprueba existencia `(root.lyrics_context_id,NEW.lyrics_ordinal)` y binding.context_id + lyrics_ordinal exactos. Toda comprobación evita semántica NULL tri-valued con `IS`/`IS NOT` cuando aplica.

La fila `analysis` original nunca se actualiza para presentar resultado nuevo ni se redefine UNIQUE(take_id,kind,analyzer_id); analyzer_version continúa **fuera** de esa clave. Una referencia legacy requiere identidad/método/analyzer/hash compatibles y queda snapshot histórico, no backfill. Resultados fallidos/missing son evidencia honesta por método y no invalidan otro método. Publicar registro Analysis outcome failed/missing usa receipt de fallo/missing y estado intent failed; nunca fabrica publication succeeded ni serving musical. El registro queda leíble por API autenticada como evidencia fallida. Resultado textual de sections declara origin=textual y no acredita segmentación medida.

Correcciones conservan todos los line_id/token_id, orden, slices/texto/context/binding/initial_result/audio y duración de la revisión raíz. Cambian sólo state/start/end/confidence y regiones justificadas; nuevo error de tokenización o texto exige **alineación inicial nueva**, no corrección encubierta. Línea user y palabras user tienen tiempos completos coherentes: no ajustar línea independientemente dejando palabras fuera. Tiempos no decrecientes por orden dentro línea; solapes entre líneas/palabras sólo si el binding composite real permite voces simultáneas, y requieren evidencia de región uncertain, no solape silencioso. No se interpola missing ni se trunca canción. La UI puede señalar confianza ausente (NULL, no1). Import mantiene tokens originales; la adopción local crea receipt import y conserva evidencia original separada.

### 4.6 Presets y VideoProject histórico

| Tabla | Columnas exactas | PK/UNIQUE y checks adicionales |
|---|---|---|
| `m3_preset_revision` | H; `preset_id U -> preset.id`; `lineage_id U`; `revision R`; `parent_revision_id U? -> m3_preset_revision.id`; `kind TEXT`; `name L`; `style_prompt TEXT`; `parameters_capture_id U -> m3_capture.id`; `visual_style TEXT`; `origin TEXT` | UNIQUE(preset_id,revision); kind style/voice/visual/full; origin user/import; primera revision1,parent NULL,lineage=id; siguiente mismo preset/owner/kind/lineage,padre+1. style_prompt/visual_style strings≤32768Unicode cada uno y payload agregado≤1MiB; vacío explícito permitido |
| `m3_preset_source` | `revision_id U -> m3_preset_revision.id`; `ordinal N`; `role TEXT`; `source_snapshot_id U -> m3_source_snapshot.id` | PK(revision_id,ordinal); UNIQUE(revision_id,role,source_snapshot_id); role timbre/reference_audio/reference_image/visual; listas≤64; owner y rights aplicables; refs efectivas, no URL/alias actual |
| `m3_preset_head` | `preset_id U PRIMARY KEY -> preset.id`; `owner_id U -> user.id`; `revision R`; `active_revision_id U -> m3_preset_revision.id` | UNIQUE(active_revision_id); head sólo sellado del preset; incremento CAS+1,parent actual. Base preset name/kind/payload editables bajo esa transacción server; sin reescribir revisiones |
| `m3_video_revision` | H; `scope_id U -> m3_scope.id`; `video_project_id U -> video_project.id`; `revision R`; `timeline_capture_id U -> m3_capture.id`; `audio_binding_id U -> m3_audio_binding.id`; `timing_revision_id U? -> m3_timing_revision.id`; `artwork_source_id U? -> m3_source_snapshot.id`; `features_source_id U? -> m3_source_snapshot.id` | UNIQUE(video_project_id,revision); timeline capture conserva bytes/hash de timeline rev exacto; audio/timing mismo binding; artwork/features exactos y rights; ausencia sólo si proyecto no consume ese componente |

PresetRevision captura valores efectivos de un preset **después de cada creación/edición** en transacción de edición/CAS; uso copia selección exacta a D-02 recipe. Primera adopción de preset legacy es explícita y nueva, con evidencia de payload observado; no backfill masivo ni afirmar revisión histórica inexistente. ParametersCapture reader `production.preset_parameters/1` descrito en §4.11 es una lista de ProfileRefs cerrados con schemas de parámetros **ratificados** por capability/profile: desconocido bloquea crear/usar revisión que lo necesita; no dict catch-all. Timbre/ref se conservan, aplicar depende de capacidad probada; no activa LoRA/F-71. Eliminar lógico del catálogo no retargetea trabajos ni borra FK; borrado físico referenciado aborta.

Video revision captura el estado observado y timeline-v1 original o reader nuevo D-04 ratificado; no relaja timeline-v1 para meter columnas extras. Snapshot rev7 sigue consumible cuando el proyecto llega rev8. G13 congela identidad/song/take del VideoProject referenciado y no bloquea editar su timeline/rev actual. Render debe guardar timeline_rev=video_revision.revision y su plan/receipt enlaza snapshot; no usa timeline actual al ejecutar.

### 4.7 Request, intención, revisión, ejecución y custodia

| Tabla | Columnas exactas | PK/UNIQUE y checks adicionales |
|---|---|---|
| `m3_request` | H; `scope_id U -> m3_scope.id`; `job_id U -> job.id`; `operation TEXT`; `subject_kind TEXT`; `result_key U`; `request_capture_id U -> m3_capture.id`; `recipe_capture_id U -> m3_capture.id` | UNIQUE(scope_id,result_key); UNIQUE(job_id,id) para vínculo explícito. subject_kind asset/analysis/artwork/render/export/import/backup; operation exactamente19parejas §4.10. Captures request/recipe1 coherentes y request_id=id,owner/job/scope/result_key exactos |
| `m3_request_source` | `request_id U -> m3_request.id`; `ordinal N`; `source_snapshot_id U -> m3_source_snapshot.id` | PK(request_id,ordinal); UNIQUE(request_id,source_snapshot_id); orden/ids/roles/sha/evidence iguales recipe.sources |
| `m3_request_parent` | `request_id U -> m3_request.id`; `ordinal N`; `take_id U -> take.id`; `root_id U -> take.id`; `audio_sha256 S`; `manifest_capture_id U -> m3_capture.id` | PK(request_id,ordinal); UNIQUE(request_id,take_id);<=64,owner/song,raíces originales canónicas, orden exacto ParentRef |
| `m3_request_rights` | `request_id U -> m3_request.id`; `ordinal N`; `rights_snapshot_id U -> m3_rights_snapshot.id` | PK(request_id,ordinal); UNIQUE(request_id,rights_snapshot_id); lista/cobertura/conjunción exactas, no sólo boolclient |
| `m3_request_revision` | `request_id U -> m3_request.id`; `ordinal N`; `kind TEXT`; `revision_id U`; `reader_version R`; `revision R`; `sha256 S` | PK(request_id,ordinal); UNIQUE(request_id,kind,revision_id); kind mix/lyrics_timing/video_project/analysis/preset. FK polimórfica G04 a mix/timing/video/analysis_result/preset exacta y sellada; revision de AnalysisResult=1 (resultado no mutable), reader_version1 para familias D-03 |
| `m3_intent` | H; `request_id U -> m3_request.id`; `scope_id U -> m3_scope.id`; `subject_kind TEXT`; `result_key U`; `request_sha256 S`; `recipe_sha256 S`; `state TEXT`; `revision R`; `active_revision_id U -> m3_intent_revision.id`; `committed_receipt_id U? -> m3_receipt.id`; `committed_at UTC?`; `error_code L?` | UNIQUE(request_id); UNIQUE(scope_id,result_key); state reserved/prepared/committed/failed/cancelled. initial revision1. committed→receipt/time NOT NULL,error NULL; failed/cancelled→receipt/time NULL,error NOT NULL; reserved/prepared todos3NULL. Identidad/captura inmutable |
| `m3_execution` | H; `intent_id U -> m3_intent.id`; `ordinal R`; `kind TEXT`; `engine_attempt_id U? -> job_attempt.id`; `handler L?`; `handler_version R?`; `selection_capture_id U -> m3_capture.id`; `start_evidence_capture_id U -> m3_capture.id` | UNIQUE(intent_id,ordinal); UNIQUE(id,intent_id,ordinal). kind engine/cpu/upload/maintenance; engine→attempt NOT NULL,handler/version NULL; demás→attempt NULL,handler/version NOT NULL del registro cerrado. Engine attempt job=request.job y real; ordinal execution no reemplaza ordinal engine |
| `m3_execution_stage` | H; `execution_id U -> m3_execution.id`; `stage TEXT`; `executor_kind TEXT`; `engine_attempt_id U? -> job_attempt.id`; `handler L?`; `handler_version R?`; `selection_capture_id U -> m3_capture.id`; `start_evidence_capture_id U -> m3_capture.id` | UNIQUE(execution_id,stage); stage raw/post/cpu/upload/maintenance; executor_kind engine/cpu/upload/maintenance. raw sólo engine con intento real, handler/version NULL; post/cpu sólo CPU sin attempt y handler/version reales; upload/maintenance sólo su clase sin attempt. Stage creado antes de su efecto y ligado a la ejecución real. No proceso ni terminal inventado |
| `m3_custody` | `execution_id U PRIMARY KEY -> m3_execution.id`; `owner_id U -> user.id`; `revision R`; `state TEXT`; `binding_capture_id U -> m3_capture.id`; `custody_evidence_capture_id U -> m3_capture.id`; `reconciliation_capture_id U? -> m3_capture.id` | state owned/unknown/released; revision inicial1,CAS+1. unknown NO terminal; released sólo evidencia reconciliación real y ningún efecto propio pendiente. Sin PID/token/lease en captura portable; contexto vivo privado separado |
| `m3_intent_revision` | H; `intent_id U -> m3_intent.id`; `revision R`; `predecessor_id U? -> m3_intent_revision.id`; `expected_revision N`; `expected_state TEXT`; `phase TEXT`; `next_state TEXT`; `execution_id U`; `execution_ordinal R`; `request_sha256 S`; `result_evidence_ref U -> m3_phase_evidence.id`; `package_capture_id U? -> m3_capture.id` | UNIQUE(intent_id,revision); FK(execution_id,intent_id,execution_ordinal)→m3_execution(id,intent_id,ordinal). Phase reserved/executing/executed/prepared/renamed/committed/failed/cancelled; expected_state absent/reserved/prepared/committed/failed/cancelled; next_state5enum. Primera revision1,expected_revision0,expected_state absent,predecessor NULL,phase reserved. Otras expected_revision=revision−1/predecessor mismo intent/rev−1; overflow aborta |
| `m3_phase_evidence` | H; `intent_id U -> m3_intent.id`; `execution_id U -> m3_execution.id`; `phase TEXT`; `capture_id U -> m3_capture.id`; `receipt_id U? -> m3_receipt.id`; `prior_evidence_id U? -> m3_phase_evidence.id` | Phase enum de intent_revision; evidence existente y misma identity/ejecución. reserved/executing receipt NULL; executed receipt éxito raw/cpu/upload, salvo maintenance que exige receipt NULL y evidence maintenance_execution propia. prepared/renamed package evidence propia; committed receipt final succeeded; failed/cancelled receipt fallo/cancel real. Predecessor evidence mismo intent y ordinal previo o actual, DAG |

Todas las estructuras de request están en recipe como única autoridad D-02; las filas son índices exactos de esa captura, no sidecars autoritativos. El seal de request valida también lyrics/selection/profiles/parameters/required_roles vía reader D-02 y referencias capturadas. Esos objetos no se reubican en top-level ni se crean clones libres. `job.request` contiene envelope/captura privada conforme integración futura; job.task/selection coherentes, no job ficticio. No hay UNIQUE global de hash, ni nueva dedup por content.

Initial reservation se inserta en **una transacción SQLite** con request sellado, intent reserved revision1, execution ordinal1 sin proceso iniciado, phase_evidence reserved y revisión1. FKs circulares diferidas permiten declarar IDs conocidos; el guard de cierre BEFORE intent INSERT exige request/evidence/execution/revision ya insertados en esa transacción (orden: request; execution/evidence/revision con intent FK diferida; intent al final). `m3_execution` antes del intent usa request local obtenido por revisión/intent pendiente: G05 valida identidades por request sellado del capture, G10 vuelve a validar en intent INSERT; no exige fila intent ya materializada para permitir esa reserva. En reserva engine_attempt_id puede referir **intento real preparado sin enviar**, ya persistido por cola M1, nunca un intento fake. Si no hay intento real reservado todavía, se reserva execution kind conforme executor sin afirmar terminal: D-02 capture enum engine obliga engine_attempt_id real antes send; la preparación de job_attempt precede al cierre de la reserva. CPU/upload/maintenance no crean JobAttempt.

La revisión reserved apunta a evidencia cerrada `production.reservation/1`: `{intent_id,request_id,job_id,request_sha256,recipe_sha256,subject:{kind,result_key},owner_id,scope,execution_id,execution_ordinal,reserved_at}`; IDs/hashes exactos y reserved_at UTC. Acredita **reserva durable prevista**, no salida ejecutada ni receipt succeeded. El valor evidence existe antes del primer efecto y la transacción debe confirmar antes send/copy/render/cut. No permite un `result_evidence_ref` NULL por conveniencia. Executing obtiene evidencia `production.execution_start/1` con reservation_ref,execution_id,ordinal,selection_ref,binding_ref,custody_ref,started_at reales; después ejecuta. Sólo executed/prepared/renamed/committed usan evidencia de hechos realmente ocurridos.

Retry explícito crea execution ordinal anterior+1 y nuevas revisiones/evidence; conserva request, result_key y todas las filas anteriores. Si engine, intento nuevo M1 real de ese job y ordinal propio, no derivado numéricamente de execution ordinal. UNKNOWN bloquea retry/cancel cleanup hasta reconciliación; estado terminal intent y custodia son ejes separados. El usuario crea otra captura/resultado con request/result_key nuevos cuando cambia params/model/preset/audio, no retry con bytes distintos.

`m3_execution.kind` identifica la selección inicial de D-02, no atribuye toda la cadena a un único proceso. Su start_evidence_capture_id inicial refiere la reserva existente; no dice que ya se ejecutó. Cada efecto real necesita `m3_execution_stage` con `production.stage_start/1` confirmado antes del efecto: `{execution_id,stage_id,stage,executor_kind,selection_ref,reservation_ref,started_at}`; selection_ref cerrado, IDs y UTC exactos. Una ejecución engine puede tener raw(engine) y post(cpu); CPU post registra herramientas/mediciones propias y nunca se atribuye al engine. Ejecución CPU admite cpu; upload admite upload y post(cpu) si requiere validación/copia; maintenance admite maintenance. Ninguna ejecución CPU/upload/maintenance admite stage raw(engine). Receipt engine_raw liga stage raw + intento/terminal real; cpu_result liga stage post/cpu real; upload_result liga stage upload real. Receipt final refiere evidencia de esas etapas y no crea etapa inventada.

Registro cerrado de handlers CPU/version1: separate_stems→`production.stems.validate`; mix_preview→`production.mix.preview`; extract_features→`production.features.extract`; analyze/align_lyrics→`production.analysis.accept`; correct_lyrics_timing→`production.timing.correct`; generate_artwork/edit_artwork→`production.artwork.validate`; attach_artwork_upload→`production.upload.attach`; render_n0→`production.video.render`; export_audio→`production.audio.export`; export_stems→`production.stems.export`; export_video→`production.video.export`; export_lyrics→`production.lyrics.export`; export_project→`production.project.export`; import_project→`production.project.import`; backup/restore/activate_library→`production.library.backup`/`production.library.restore`/`production.library.activate`. Son identidades privadas **a implementar y liberar**, no handlers disponibles hoy. El nombre no lleva comando/ruta/código cliente. Stage CPU y selección inicial CPU usan sólo su handler de la pareja; stage raw exige descriptor/capability de la selección engine congelada. Upload/maintenance usan handler de su acción, sin attempt/model/seed. Se valida disponibilidad de handler/reader/component por release D-12 antes de efecto.

### 4.8 Recibos, sellos y resultados tipados

| Tabla | Columnas exactas | PK/UNIQUE y checks adicionales |
|---|---|---|
| `m3_receipt` | H; `intent_id U -> m3_intent.id`; `execution_id U -> m3_execution.id`; `execution_ordinal R`; `stage_id U? -> m3_execution_stage.id`; `kind TEXT`; `outcome TEXT`; `intent_revision R?`; `capture_id U -> m3_capture.id`; `error_code L?`; `finished_at UTC` | FK(execution_id,intent_id,execution_ordinal)→execution triple; FK(intent_id,intent_revision)→intent_revision(intent_id,revision) si NOT NULL. kind engine_raw/cpu_result/upload_result/publication/import/maintenance; outcome succeeded/failed/cancelled. succeeded→error NULL; otros→error NOT NULL. final publication/import/maintenance exige intent_revision y stage NULL; raw/cpu/upload exige revision NULL y stage real correspondiente. UNIQUE(stage_id,kind) para terminal por etapa. Capture exacto ProductionReceipt1 D-02 |
| `m3_receipt_artifact` | `receipt_id U -> m3_receipt.id`; `ordinal N`; `role L`; `path P`; `sha256 S`; `media_type L`; `bytes N` | PK(receipt_id,ordinal); UNIQUE(receipt_id,role,path); catálogo exacto capture.artifacts y roles requeridos; no manifest/receipt autorreferente; fallidos sólo parciales propios privados |
| `m3_seal` | H; `kind TEXT`; `root_id U`; `capture_id U -> m3_capture.id` | UNIQUE(kind,root_id); UNIQUE(capture_id). kind source/rights/lyrics/audio/stems/mix/analysis/timing/preset/video/request/receipt/result. Root polimórfico **cerrado** G04, existencia y owner/scope; capture sólo de reader específico §4.11 y bytes exactamente iguales a proyección ordenada root+children. Una raíz tiene un sello, nunca se sobrescribe |
| `m3_result` | H; `intent_id U -> m3_intent.id`; `scope_id U -> m3_scope.id`; `result_key U`; `kind TEXT`; `role L`; `asset_id U? -> asset.id`; `analysis_result_id U? -> m3_analysis_result.id`; `timing_revision_id U? -> m3_timing_revision.id`; `artwork_id U? -> artwork.id`; `render_id U? -> render.id`; `export_id U? -> export.id`; `import_capture_id U? -> m3_capture.id`; `backup_capture_id U? -> m3_capture.id`; `temporary_capture_id U? -> m3_capture.id`; `publication_receipt_id U -> m3_receipt.id` | UNIQUE(scope_id,result_key,role); kind7enum; EXACTAMENTE1destino: asset→asset XOR temporary; analysis→analysis_result XOR timing; artwork/render/export exactslot; import/backup exactcapture. Owner/scope/receipt/result_key/operation exactos. No expansiónAsset.enum; import/backup no entidad musical ficticia |

El polimorfismo de `m3_seal`, `m3_rights_snapshot` y RevisionRef queda validado por INSERT y referencias inversas a tablas enumeradas. No existe una FK genérica a un ID desconocido; G04 enumera cada rama, exige `EXISTS` con owner y scope, protege UPDATE/DELETE del destino. SQL direct desconocido aborta; no reader string dinámico ni identificador SQL proporcionado por cliente. `m3_seal` permite **armado insert-only** de una raíz privada aún no consumible: contenido/children nunca se actualiza ni elimina; sólo INSERT de children antes de sello. Una raíz sin sello no es revisión válida, no se usa en request/head/intent/result/serving. Seal valida cierre completo y luego impide cualquier INSERT hijo adicional. Dos assemblers compiten por UNIQUE, perdedor rollback completo. Un armado incompleto durable se conserva privado e inerte, no se sirve ni se rellena silenciosamente.

Parent sellado no equivale por sí solo a parent publicado. Para consumir fuente musical M3, G04/G09 exige además receipt final propio e intent committed, excepto preview dentro de su autorización temporal explícita; datos legacy usan su autoridad histórica real. Dentro de una única transacción final se permite ensamblar/sellar entidades y roots nuevos todavía no committed, pero sólo el UPDATE intent final G10/G11 autoriza su cierre y visibilidad. Rollback elimina ese armado no confirmado. Un stem_set sellado con rawreceipt solamente no autoriza downstream ni serving hasta el commit de sus4Asset/resultroles. Fallos/missing Analysis sólo se exponen como evidencia honesta autenticada, nunca fuente musical success.

Result rows se insertan al commit final con sus entidades reales y receipt final en la misma transacción, excepto preview temporal y evidencia analysis failed/missing conforme abajo. El ID result_key es reserva de la unidad, **no necesariamente** PK de cada entidad; mappings explícitos aseguran roles exactos y evitan colisión por retag. Success de4stems sólo tras4assets vinculados al Take y m3_stem_set sellado completo, ningún asset parcial visible como resultado M3. Para Analysis sin medio, no se crea Asset analysis. Para import/backup, capture de closure/cut/binding da evidencia privada, sin Asset import/backup ni Song/Take fake.

Temporary preview usa resultkind asset + temporary_capture, `m3_intent.state=prepared`, receipt cpu_result succeeded, **sin publication succeeded ni committed**; no es resultado durable publicado. Temporal consumible sólo por API privada T14 con expiry/context/CAS/custodia vivos; fila se conserva histórica y deja de servirse al expirar/revocar/cancelar, no se convierte en Asset. La lectura de result exige branch operación mix_preview, nunca otras asset operations. Su role exacto preview; la fila/sello temporal no habilita import/portable. Analysis failed/missing sólo inserta AnalysisResult sellado y evidencia de fallo bajo intent failed; **no m3_result publicado**, ningún finalreceipt succeeded. Correct timing publica timing_revision nuevo bajo subject analysis, sin reescribir initial AnalysisResult.

Terminal publication de metadata pura exige ejecución real de corrección/captura y closure, aun sin artifacts: ausencia de medio no equivale a inferencia ficticia. Todos los receipts usan ramas D-02 engine_raw/cpu_result/upload_result/publication/import/maintenance exactas. FailureEvidence conserva boundary/observed_state/prior_evidence reales; UNKNOWN no se fabrica como outcome succeeded/failed. Rawreceipt nuevo no reemplaza terminal JobAttempt M1; la evidencia debe coincidir con intento/ordinal/terminal seq/hash ganador real.

### 4.9 CAS, fases, cancelación y replay

| Desde estado/fase | Hacia estado/fase | Evidencia y condición exacta |
|---|---|---|
| ausente | reserved/reserved revision1 | Request sellado, reservation1 existente y execution ordinal1; confirmar antes del primer efecto |
| reserved/reserved | reserved/executing | Misma ejecución; execution_start real, custodia owned, binding/admisión actuales; sin cancel solicitado |
| reserved/executing | reserved/executed | Receipt real engine_raw/cpu_result/upload_result succeeded; maintenance usa evidence de acción ejecutada con receipt NULL. No publication |
| reserved/executed | prepared/prepared | Paquete/cierre/medios/mediciones completos; package_capture NOT NULL, paths/roles válidos y evidence prepared existente |
| prepared/prepared | prepared/renamed | Sólo medios promovidos: no-clobber, rename y barreras reales del seam liberado. Metadata sin rename pasa directamente a commit |
| prepared/prepared o prepared/renamed | committed/committed | Final receipt succeeded, entidades/resultset completos y sellados, custodia/binding/CAS actuales; committed_at igual receipt. Import materializa Song/cierre indivisible; maintenance acredita cut/binding/rollback de su acción |
| reserved o prepared sin commit | failed/failed o cancelled/cancelled | FailureReceipt/código/prior evidence reales, sin negar commit ocurrido. UNKNOWN conserva incertidumbre y recursos incluso ante error observado; cleanup prohibido |
| failed o cancelled | reserved/reserved | Retry explícito autorizado tras reconciliación, sin efecto pendiente; nueva execution ordinal+1, mismas capturas/result_key y cursor revision+1, sin reinicio a1 |
| committed/committed | committed/committed | Sólo lectura/replay mismo receipt; **no UPDATE** ni nueva revisión/ejecución |

Mix_preview termina la ejecución CPU y pasa executed→prepared para API temporal. Invalidación/expiry usa fase cancelled con código PRODUCTION_CANCELLED y evidencia propia de invalidación real; fallo real usa failed. No crea publisher ni receipt final success. El job preview puede ser succeeded por CPU mientras intent prepared permanece temporal; no se reinterpreta como publicación durable. Mantenimiento usa `production.maintenance_execution/1` (reader D-09 liberado) para hechos de cut/copia/validación, con receipt NULL en executed. **Maintenance succeeded final** sólo existe con revision committed y acción completa. La excepción fase/evidence está discriminada por backup/restore/activate, sin receipt anticipado ni catch-all.

`m3_intent_revision` registra expected_revision y expected_state, predecessor_id, next_state y fase. BEFORE INSERT para revisiones>1 exige actual `intent.revision=expected_revision`, `intent.state=expected_state`, `intent.active_revision_id=predecessor_id`. Cursor UPDATE exige NEW.revision=OLD.revision+1<=MAX y revisión nueva perteneciente al intent con exactamente esos expected/predecessor; también owner/scope/request/recipe/hash/subject/result_key idénticos. La sentencia caller debe incluir WHERE de **todos** estos valores y affected_rows=1; un0 genera CAS_CONFLICT y rollback del armado de nueva revisión. Trigger aborta update directo sin contenido correspondiente. No se usa Song.rev como sustituto. Head Mix/Timing/Preset/Analysis sigue misma comparación OLD.revision y OLD.active.

Cancel se serializa con commit final: guard observa `job.cancel_requested_at IS NULL` para send/start/prepared/rename/commit; cancel previo bloquea. Si commit confirmó primero, replay del finalreceipt prevalece ante cancel tardío/ACK perdido sin democión. Finalize y requestcancel participan en transacción de writer SQLite; ambos no pueden ganar una snapshot WAL obsoleta: lock failure rollback completo y reread con CAS, sin reejecutar efecto. Rename no se deshace sólo porque UPDATE perdió CAS: queda propio bajo intención y custody, reconciliación antes de cualquier retry.

Crash después de rename y antes de commit conserva medios propios no servibles y su intención/custodia/evidencia. Comparar contexto completo y finalpath no-clobber; no adoptar por hash/path. Rename incierto produce custody unknown, sin receipt inventado. Commit durable con respuesta perdida se lee y devuelve exactamente receipt/resultset original, sin regenerar, copiar ni repetir commit. Disco lleno o close/flush UNKNOWN conservan evidencia y bloquean liberación. La máquina de estados no acredita exclusión Ollama ni atomicidad FS+SQLite: esas autoridades requieren seams reales liberados D-12/K1/D-09.

### 4.10 Las19parejas y vínculos resultantes

| operation | subject | Destino tipado autorizado y guard de scope |
|---|---|---|
| separate_stems | asset | Song existente;4Asset take roles stem:* + stem_set sellado; no resultado parcial |
| mix_preview | asset | Song existente;temporary_capture preview cpu_result;ningún Asset job ni commit/publication |
| extract_features | asset | Song existente;Asset take del audio_binding final con roles D-07; reader features cerrado antes ejecutar |
| analyze | analysis | Song existente;AnalysisResult method beats/sections/key/loudness,receipt real; failed/missing evidencia sin publication success |
| align_lyrics | analysis | Song existente;AnalysisResult lyrics_timing y TimingRevision initial ligados al mismo audio/context; puede resultar failed/missing |
| correct_lyrics_timing | analysis | Song existente;TimingRevision hija initial_result/audio/context invariables,cpu_result real |
| generate_artwork | artwork | Song existente;Artwork generated + sus Asset artwork,roles requeridos; engine real |
| edit_artwork | artwork | Song existente;Artwork nuevo generado + antecedente fuente autorizado; no overwrite |
| attach_artwork_upload | artwork | Song existente;Artwork upload + sus Asset,upload_result real;modelo/seed/job_attempt inexistentes |
| render_n0 | render | Song existente;Render ligado a VideoRevision/audio/timing + Asset render;cpu/browser real |
| export_audio | export | Song existente;Export audio,Asset export;original→target NULL baseline,otros targetenum exacto;perfil target capturado distingue original |
| export_stems | export | Song existente;Export stems,Asset export,ZIP completo,perfil D-05 |
| export_video | export | Song existente;Export video desde Render propio committed y Asset export |
| export_lyrics | export | Song existente;Export lyrics,Asset export,LRC/SRT desde TimingRevision exacta |
| export_project | export | Song existente;Export project_zip,Asset export,cierre D-08 exacto |
| import_project | import | Song scope destino reservado/real;import_capture closure+identitymap+receipt propio;commitSong/Take/refs íntegro,ninguna Asset import |
| backup_library | backup | Library;backup_capture cut+catalog+package+receiptmaintenance;ninguna Song/Take/Asset backup |
| restore_library | backup | Library destino nuevo;backup_capture validación+corte+package+binding;historia inerte |
| activate_library | backup | Library;backup_capture bindingprevio/nuevo+rollback+backuprestaurable exclusivo;reader D-09 ratificado |

CHECK operation/subject es disyunción literal de esas19filas; no se acepta operation nueva por string reader registrado. `m3_request` SongScope existente es obligatorio para16operaciones, salvo import_project que admite reserva Song; las3maintenance exigen LibraryScope. Preview no importable; import/package sources no exigen Take ficticio; rights cover y conjunction se verifican sobre inputs/padres/letra/tools y modelo efectivamente usados, nunca modelo de padre atribuido a CPU. La cláusula count16 incluye15operaciones Song noimport másimport=16; no inferir Song para3library.

### 4.11 Readers cerrados y registro en cada conexión

| Reader/version D-03 | Schema cerrado y proyección |
|---|---|
| `production.request/1`, `production.recipe/1`, `production.receipt/1` | Objetos D-02 ratificados íntegros;19parejas,7sujetos,ramas exactas,cuotas y privacy. Header/controlvalues iguales SQL; no completar campos fuera recipe |
| `production.source/1`, `production.rights/1` | Columnas de sus roots, destino discriminado, evidence CapturedRef/HistoricRef exacta; sin path ejecutable ni authority activa |
| `production.lyrics_context/1` | root/context+members/bindings ordenados; versiones/texto/declaraciones exactos,map/evidence tipados; none/single/composite checks §4.3 |
| `production.audio_binding/1`, `production.stem_set/1` | Campos/miembros §4.3/4.4;hash/formato/frames/duración medidos,recibos reales y referencias selladas |
| `production.mix_revision/1` | root+4controles en orden fijo vocals,drums,bass,other;lineage/revision,parent/capturaSet;bools y gain estrictos |
| `production.analysis_result/1` | Columnas §4.5,method/outcome/origin,refs/data/failure discriminados. Datos del método usa reader externo específico D-06, nunca dictlibre |
| `production.lyrics_timing_revision/1` | root+lines/words/regions ordenados;tokens/slices/bindings/states/times/confidence exactos según §4.5;corrección compara rootpadre |
| `production.preset_revision/1` | root+sourceRefs ordenadas+parametersRef;ningún alias mutable |
| `production.preset_parameters/1` | `{schema_version:1,profiles:[ProfileRef...]}`;roles únicos≤16,TypedValue ratificado D-02 por profile;no extra/default. Valores/style refs del root, no comandos/seedsfabricados |
| `production.video_revision/1` | Columnas §4.6 + HistoricRef timeline exacto/audio/timing/features/artwork;reader timeline original sin relax |
| `production.reservation/1`, `production.execution_start/1` | Campos cerrados de §4.7;reserva prueba intención y start prueba inicio,ningún output/terminalanticipado |
| `production.execution_selection/1`, `production.stage_start/1` | Selection es exactamente la rama D-02 congelada sin runtime lease/PID. Stage_start tiene campos cerrados del párrafo de §4.7 y registra etapa real, no un terminal |
| `production.prepared/1` | `{intent_id,request_sha256,recipe_sha256,execution_id,execution_ordinal,subject,package_ref,execution_evidence_ref,prepared_at}`;package completo reader D-04 por sujeto,gate antes consumir |
| `production.rename/1` | `{intent_id,execution_id,execution_ordinal,package_ref,prepared_evidence_ref,physical_receipt_ref,renamed_at}`;recibo físico propio reader K1/seam liberado;no inventar flush/rename. Metadata sin efectos FS omite fase rename |
| `production.failure/1` | `{intent_id,execution_id,execution_ordinal,receipt_ref,observed_state,prior_evidence_ref}`. observed_state failed/cancelled/unknown; prior_evidence_ref CapturedRef o NULL explícito. ReceiptRef refiere ProductionReceipt1 failed/cancelled real con FailureEvidence D-02. No output ni terminal ficticio |
| `production.result/1` | Root + destino único tipado/role/ref/receipt según §4.8;preview rama temporalD14,importD08,backupD09 gatingexplícito |

Schemas internos D-03 son **proyección exacta de columnas y children anteriores**, con campos JSON reservados `seal_kind=<m3_seal.kind>` y `schema_version=1`, nombres de campo SQL y valores escalares SQL con el tipo JSON correspondiente; los IDs FK siguen ULID y los hashes siguen SHA, no se sustituyen por otro objeto silenciosamente. `kind`, cuando existe en el root o en un child, conserva exactamente su columna y enum SQL: no es el discriminante del sello. CapturedRef/HistoricRef D-02 son wrappers exteriores para referir esos bytes o permanecen dentro de los objetos D-02 originales. Esta regla se aplica a las once familias internas nuevas D-03, **excepto** request/recipe/receipt y payloads históricos/perfiles: éstos conservan su schema original ratificado y no reciben `seal_kind` ni campos SQL adicionales. Su seal verifica la proyección SQL hacia los campos originales D-02 (por ejemplo receipt_id=id, campos intent sólo en evidence de rama final, nunca arriba). Así no se expande D-02 por conveniencia del ORM.

El seal calcula bytes canónicos con child arrays por ordinal o roles ordenados fijados. En objetos D-03 nuevos todos los campos de la tabla son obligatorios, incluidos los NULL explícitos de columnas nullable; no optional/default implícito. CapturedRef/HistoricRef D-02 mantienen su schema original. Una captura no se busca globalmente sólo por SHA: su FK/dependency identifica evidencia del mismo owner/cierre/scope. Head/intent/custody no se serializan como revisión de contenido ni son portables.

Esquema exacto del seal nuevo: columnas del root como campos top-level más `seal_kind`/`schema_version`; arrays hijos sólo cuando aplica: lyrics→`members`,`bindings`; stems→`members`; mix→`stems`; timing→`lines`,`words`,`regions` (words ordenados por ordinal de línea y luego palabra); preset→`sources`; source/rights/audio/analysis/video/result no tienen arrays hijos. Cada elemento de array tiene todas las columnas de su tabla hija, incluidos IDs/FK y NULL explícitos. Orden: ordinal ascendente; mix/stems orden fijo vocals,drums,bass,other; timing words por line.ordinal y word.ordinal. No se serializa m3_seal.id/capture_id dentro de su propio payload, ni SHA autorreferente. H del root sí se conserva. Request/receipt tienen arrays/campos **D-02**, validados contra sus índices/artifacts SQL, sin arrays nuevos.

#### FIX1 B01 — campos exactos, namespace reservado y dominios de hash

ROOT seleccionó el2026-10-11T20:11:41.906146+00:00 este ajuste mínimo dentro de PD-O1. La fuente anterior SHA `f982b1bd9c3fc181034911902c9b39dc29943266be8b56941c5ac4b9b6b56d46`,105751bytes, permanece readonly. Era un contrato propuesto no adoptado: su proyección ambigua no es una versión histórica persistida. La definición corregida es la única representación nueva de estos readers `/1`; no se crea alias, versión legacy, fallback ni migración de bytes anteriores. Readers históricos v1/v2 y D-02 no cambian.

La siguiente tabla fija el conjunto top-level **completo** por familia. `H` significa únicamente `id,owner_id,created_at`, ya definido en §4.1, y se expande como tres campos JSON, nunca como objeto `H`. Cada fila añade exactamente `seal_kind,schema_version` a sus campos root; la última columna enumera los únicos arrays adicionales obligatorios, incluidos arrays vacíos permitidos por los counts de la familia. No hay un campo `kind` añadido a roots que carecen de él. Tipos/nullability/enums/refs siguen las tablas SQL §4.2–4.8; se conserva todo campo nullable como NULL JSON explícito. La tabla es notación documental, no helper ejecutable ni extensión dinámica del schema.

| seal_kind literal / root | Campos root completos además de H | Arrays y tipo exacto de cada row |
|---|---|---|
| source / m3_source_snapshot | scope_id,kind,source_id,role,sha256,media_type,bytes,evidence_capture_id,asset_id,upload_id,analysis_id,analysis_result_id,artwork_id,render_id,export_id,package_capture_id | Ninguno |
| rights / m3_rights_snapshot | scope_id,ref_kind,entity_kind,entity_id,pin_id,kind,declaration,real_person,consent,commercial_use,sha256,evidence_capture_id | Ninguno |
| lyrics / m3_lyrics_context | scope_id,take_id,kind,origin_capture_id | members: todas las columnas de m3_lyrics_member; bindings: todas las columnas de m3_lyrics_binding, H expandido incluido |
| audio / m3_audio_binding | scope_id,take_id,kind,asset_id,mix_revision_id,audio_sha256,sample_rate,channels,frames,duration_s,measurement_capture_id,execution_receipt_id,media_capture_id | Ninguno |
| stems / m3_stem_set | scope_id,take_id,input_audio_binding_id,result_key,execution_receipt_id | members: todas las columnas de m3_stem_member |
| mix / m3_mix_revision | scope_id,take_id,set_id,lineage_id,revision,parent_revision_id,origin | stems: todas las columnas de m3_mix_stem |
| analysis / m3_analysis_result | scope_id,take_id,audio_binding_id,result_key,method,analyzer_id,analyzer_version,origin,outcome,lyrics_context_id,legacy_analysis_id,data_capture_id,execution_receipt_id,error_code | Ninguno |
| timing / m3_timing_revision | scope_id,take_id,initial_result_id,audio_binding_id,lyrics_context_id,lineage_id,revision,parent_revision_id,origin,execution_receipt_id | lines: todas las columnas de m3_timing_line; words: todas las columnas de m3_timing_word; regions: todas las columnas de m3_timing_region |
| preset / m3_preset_revision | preset_id,lineage_id,revision,parent_revision_id,kind,name,style_prompt,parameters_capture_id,visual_style,origin | sources: todas las columnas de m3_preset_source |
| video / m3_video_revision | scope_id,video_project_id,revision,timeline_capture_id,audio_binding_id,timing_revision_id,artwork_source_id,features_source_id | Ninguno |
| result / m3_result | intent_id,scope_id,result_key,kind,role,asset_id,analysis_result_id,timing_revision_id,artwork_id,render_id,export_id,import_capture_id,backup_capture_id,temporary_capture_id,publication_receipt_id | Ninguno |

Namespace top-level reservado cerrado: `{seal_kind,schema_version,members,bindings,stems,lines,words,regions,sources}`. Sólo los dos primeros pertenecen a todas las once familias; los demás existen únicamente en las filas que los enumeran. No es un permiso para aceptar cualquier clave de esa lista en cualquier familia. Ninguna de las40listas de columnas SQL, tras expandir H, usa esos nombres; tampoco el header SQL de m3_capture `id,owner_id,created_at,scope_id,family,reader,version,payload,sha256,bytes` los usa. La comprobación de disyunción cubre también tablas hijas, heads, scope, execution, receipt y seal, aunque no todas tengan payload propio. `kind` no pertenece al namespace reservado: su uso SQL es legítimo, también en m3_timing_region. Un nombre reservado desconocido (`seal_type`, `seal_version`, `seal_other`, etc.), un array no aplicable o cualquier extra rechaza. Un futuro campo SQL que colisione con el namespace exige decisión/schema nuevo previo; no se permite resolverlo mediante overwrite, nesting automático o alias.

La proyección primero valida nombres únicos y disyuntos y luego exige exactamente el conjunto de su fila: ningún merge puede sobrescribir un campo root. El parser detecta **duplicate keys en todos los objetos antes de construir mapas**, incluidas repeticiones con igual valor o escapes que decodifiquen al mismo nombre. No hay política first/last wins. `seal_kind` es string literal de la fila, `schema_version` es int estricto1 (no bool ni string); la identidad SQL de G09 debe coincidir con esos dos valores y con capture.reader/version/family del mapping cerrado. El lector no infiere familia por root.kind, ausencia de campos o contenido de un hash. Campos root, rows tipadas, counts, orden y NULLs son completos; no extras, gaps ni defaults. Request/recipe/receipt mantienen sus objetos D-02 completos; añadirles `seal_kind` es extra y rechaza. Los schemas de profiles, phase/reservation y payloads historic conservan sus propios conjuntos cerrados; este namespace no les añade campos.

Canónico privado: se aplica sin cambios el formato canónico D-02/§4.1, UTF-8 sin BOM, parsing estricto y orden de arrays antes fijado. `m3_capture.payload` contiene esos bytes completos; `m3_capture.bytes=length(payload)` y `m3_capture.sha256=SHA256(payload)`. El hash de un sello nuevo cubre **ambos** discriminantes cuando root.kind existe, todos los campos root/H, NULLs y cada campo de cada row ordenada. No se omite seal_kind del dominio ni se hashea sólo contenido musical. Source/rights root.sha256, audio_sha256, hashes de miembros y evidence refs conservan su dominio previo de fuente/evidencia: no se reemplazan por el hash del JSON del sello. Header m3_capture y m3_seal.id/capture_id no se incluyen en su propio payload; no se introduce hash autorreferente. Las refs nuevas CapturedRef/RevisionRef, m3_request_revision.sha256 y dependencies que apunten a una captura nueva identifican su hash canónico completo corregido; no se actualizan capturas históricas, refs ya persistidas ni firmas originales. SHA continúa acreditar bytes y no derechos, medición, custodia ni autoridad.

G02 valida schema/canonical/hash del reader exacto; G09 reconstruye la proyección tipada de la raíz SQL y children en esa conexión, valida `seal_kind=NEW.kind` sin tocar root.kind y compara los bytes completos con capture.payload, además de su header/hash y todos los guards de cierre. Para request/receipt ejecuta la proyección original D-02, sin seal_kind. Captura JSON válida con valores distintos de SQL también aborta. UPDATE/DELETE root/child/capture y overwrite continúan prohibidos; el ajuste no cambia columnas, FK, nombres SQL, CAS, inversas ni visibilidad.

#### Casos documentales FIX1 para PD-01/04/10/17

Estos casos especifican fixtures **futuras** sobre rows existentes/armadas autorizadas con evidence, owner/scope y guards satisfechos; no son un harness escrito ni ejecutado. Para cada fila anterior, el positivo se representa como su objeto exacto: H expandido, todos los campos root con tipos de §4.1 y NULLs propios, seal_kind literal, schema_version1 y sus arrays completos con rows del tipo enumerado. Esa definición da once positivos completos; los siguientes fragmentos JSON son únicamente el par de discriminantes visible, **no payloads suficientes por sí solos**.

| Familia | Fragmento del positivo; restantes campos/rows son los exactos de la tabla |
|---|---|
| source | `{"kind":"asset","seal_kind":"source","schema_version":1}`; también upload/analysis/artwork/render/export/package con XOR correspondiente |
| rights | `{"kind":"audio","seal_kind":"rights","schema_version":1}`; también image/lyrics/parent/tool/model con declaración/ref/consent propios |
| lyrics | `{"kind":"single","seal_kind":"lyrics","schema_version":1}`; none con arrays members/bindings vacíos; composite con members/bindings medidos completos |
| audio | `{"kind":"master","seal_kind":"audio","schema_version":1}`; master asset real y mix_revision/execution_receipt NULL; mix con revisión y receipt CPU reales, asset NULL |
| preset | `{"kind":"style","seal_kind":"preset","schema_version":1}`; también voice/visual/full, sources ordenadas y parameters_capture_id ratificado |
| result | `{"kind":"asset","seal_kind":"result","schema_version":1}`; también analysis/artwork/render/export/import/backup con slot/role/receipt/scope propios |
| stems/mix/analysis/timing/video | Sólo seal_kind literal stems/mix/analysis/timing/video respectivamente y schema_version1; **no kind top-level**. Timing.regions conserva kind instrumental/uncertain dentro de cada row |

Ejemplo tipado audio master completo en notación documental: H=`id=A,owner_id=O,created_at=T`; `scope_id=S,take_id=K,kind="master",asset_id=X,mix_revision_id=NULL,audio_sha256=Q,sample_rate=48000,channels=2,frames=48000,duration_s=1.0,measurement_capture_id=M,execution_receipt_id=NULL,media_capture_id=C,seal_kind="audio",schema_version=1`. A/O/S/K/X/M/C son ULID concretos de las rows reales del caso, T UTC y Q SHA256 medido; las letras de esta explicación no son valores aceptados ni defaults. El objeto JSON del fixture futuro contiene los16campos root/H de esa notación más los dos campos reservados, sin arrays. Cambiar sólo kind a mix falla por XOR/receipt; un positivo mix tiene mix_revision_id y execution_receipt_id reales y asset_id NULL. El parser y G09 deben aceptar el par master/audio sin confundir ninguno.

| Negativo futuro | Rechazo exacto exigido |
|---|---|
| Representación anterior sólo kind; audio kind=master o kind=audio sin seal_kind | Falta seal_kind; kind=audio además viola enum master/mix. Sin reader legacy ni inferencia de tipo |
| JSON contiene dos kind, dos seal_kind, dos schema_version o duplicate key de cualquier root/row | Rechazo antes de mapa/hash/SQL, incluso valores iguales; no overwrite |
| Escritor pisa audio.kind con audio, source.kind con source, rights.kind con rights, lyrics.kind con lyrics, preset.kind con preset o result.kind con result | Enum root inválido; ninguna de las seis colisiones se tolera |
| seal_kind de otra fila (p.ej master con seal_kind=source), ausente, NULL, bool o string desconocido | Schema/reader y G09 rechazan; m3_seal.kind/reader/root no coinciden |
| En stems/mix/analysis/timing/video se añade kind top-level; timing child.kind se renombra seal_kind | Extra top-level o gap/extra de row tipada; no promoción/renombrado de kind hijo |
| Campos extras/reservados desconocidos, array no aplicable; falta H, root nullable NULL explícito, array obligatorio o columna de row | Conjunto exacto no coincide; ninguna reparación ni default |
| schema_version0/2/desconocida, bool/string1; capture.version2, reader ajeno o family distinta | Dispatch cerrado rechaza, sin convertir versión; histórico continúa por reader original |
| JSON completo parseable pero kind/id/hash/ref/child/orden/NULL distinto de SQL; SHA calculado sin seal_kind | G02/G09 y guards relacionales abortan, sin sello/consumo |
| seal_kind insertado en request/recipe/receipt D-02, profile/phase/historic original o wrapper exterior | Extra bajo su schema propio; sin cambiar enum/schema D-02 ni historia |

El positivo para cada una de las once familias debe comprobar igualdad completa SQL→bytes→reader, hash/header y consumo sólo con autoridad de su fase; cada negativo se parametriza sobre todas las familias a las que aplica, no sólo audio ni los seis pares. Request/receipt tienen positivos separados D-02 y negativos de campo reservado extra. Las otras29tablas conservan sus campos exactos y sus guards sin crearles una proyección de contenido nueva.

Mapping cerrado seal kind→root/reader/family capture: source→m3_source_snapshot/production.source/revision; rights→m3_rights_snapshot/production.rights/rights; lyrics→m3_lyrics_context/production.lyrics_context/revision; audio→m3_audio_binding/production.audio_binding/measurement; stems→m3_stem_set/production.stem_set/revision; mix→m3_mix_revision/production.mix_revision/revision; analysis→m3_analysis_result/production.analysis_result/revision; timing→m3_timing_revision/production.lyrics_timing_revision/revision; preset→m3_preset_revision/production.preset_revision/revision; video→m3_video_revision/production.video_revision/revision; request→m3_request/production.request/request; receipt→m3_receipt/production.receipt/execution para raw/cpu/upload,publication para publication/import/maintenance; result→m3_result/production.result/publication salvo preview que usa phase. Todos version1. production.recipe usa family recipe; production.reservation usa reservation; production.execution_start/production.execution_selection/production.stage_start/production.prepared/production.rename/production.failure usan phase. Reader con otra family rechaza; no interpretación por nombre libre.

Reader de root source Analysis describe los bytes originales del payload Analysis histórico o del data_capture nuevo (media_type application/json y bytes/hash exactos de esa evidencia), no un archivo de audio inexistente. Outcome failed/missing no crea SourceRef consumible succeeded. Package/closure/rights pin IDs se resuelven por sus readers ratificados y evidencia local capturada; no FKs a Song/Take inventados. Import preserva los bytes/IDs/owner históricos de evidencia original en capture historic; owner local y mapping de filas locales son autoridad de import propia y no reescritura del original. Cualquier proyección remapeada nueva tiene sello/hash propios y conserva el original separado, con mapping autorizado D-08.

G02 llama función SQL registrada `m3_validate_capture(family,reader,version,payload,sha256,owner_id,scope_id)` que devuelve1 **sólo** tras parsing estricto+schema+SHA+cuotas y registra error sanitizado; G09 llama `m3_validate_seal(kind,root_id,capture_id)` que compara proyección completa y todas invariantes relacionales de tablas anteriores. Cualquier excepción, reader/version desconocida o dependencia ausente devuelve0/abort; ninguna función consulta red/FS/ejecuta modelos ni toma hash como autoridad. Las validaciones relacionales puras usan la misma conexión writer/snapshot, sin segundoengine que vea estado antiguo. Triggers locales SQL `EXISTS`/count/CHECK/FK también protegen claves/owner/CAS independientemente de DTO. Estas funciones son requisitos de implementación futura, no disponibles ni ejecutadas en este trabajo.

Registro **antes de preparar/escribir** en todas conexiones: serverORM, worker, Alembiconline, importer/restorevalidator,backup/mantenimientowriter,toolingSQLautorizado,fixturesytests. Conexión nueva sinfunción provoca `no such function` al tocar captures/seals y falla cerrada; `PRAGMA foreign_keys=ON` obligatorio antesBEGIN,verificado cada checkout. Schema/head/triggerinventory se verifica al iniciar; falta guard bloquea escritura. No permitir `PRAGMA foreign_keys=OFF`,DROPTRIGGER,`writable_schema` ni REPLACE en conexiones producto. Herramienta con privilegio de reemplazar schema queda fuera del boundary de seguridad de SQLite, requiere mantenimiento autorizado; no se afirma resistencia a administradorhostmalicioso.

Registro externo cerrado pendiente: D-04 package/publication por sujeto e históricos nuevos; D-05 mix/audioexport/stemsexport mediciones; D-06 analysis_method/alignment + mediciones; D-07 features/render/scenebinding; D-08 catalog/closure/identitymap/portable; D-09 librarybinding/cut/maintenanceexecution/restorevalidation/rollback. D-11 workflow/artworkcapability y T14temporalpreview mantienen gate propio. Registro de esos readers exige nombre/versión/schema/SHA liberados por ROOT,D-12; hasta entonces la operación concreta que losconsume rechaza DEPENDENCY_UNAVAILABLE **antes efectos**. D-03 no deja en esos gates su propio schema SQL/tokens/revisions/phases/CAS. No hay fallback aJSONlibre,dictpresets ni handlercustom delcliente.

### 4.12 Catálogo exacto de guards y comprobaciones inversas

La regla de expansión es normativa: para **cada FK/slot/ref** anterior se emiten G01/G04 y su inversa G13; para **cada root/child** G06/G09; para **cada head/cursor** G10. No basta un muestreo. Pertenencia transitiva se resuelve por JOIN fijo: child→root→scope.song_id o global NULL; Asset→entity_song; Analysis→Take; Render→VideoProject; Timing→context/audio; Request→scope; Receipt/Result→intent. En reserva de import, scope_key es el Song previsto, no una fila ficticia.

| Guard | Momento/objetos | Predicado exacto que debe pasar / protección inversa |
|---|---|---|
| G01 identidad/tipos | BEFORE INSERT de todas las tablas; BEFORE UPDATE de mutables | Checks §4.1 para H, FK, SHA, bools, tipos/rangos/UTC/paths/enums; owner existente. UPDATE no cambia identidad, scope, lineage, result_key ni hashes. Excepción única: materializar scope.song_id en commit import |
| G02 bytes/reader | BEFORE INSERT capture y scope library | validate_capture=1, length=bytes, SHA y reader/version exactos, gate existente. Historic conserva bytes originales. UPDATE/DELETE capture denegados |
| G03 DAG/padre | BEFORE INSERT dependency/binding/revisiones con parent | Padre existente o ciclo diferido cerrado antes de consumo, mismo owner/scope. WITH RECURSIVE no alcanza NEW.id; parent.revision+1 sin overflow. Raíces Take originales se conservan; referir fragmento no crea arista nueva |
| G04 referencia forward | BEFORE INSERT de cada FK/slot/ref y UPDATE mutable | EXISTS destino tipado con owner y scope compatibles; globals sólo rama permitida; XOR/nulls exactos; kind/method/subject/role/receipt coherentes. Ciclos reservación/final se validan en G10 antes de commit; consumo requiere seal y publicación válida |
| G05 request/scope | BEFORE INSERT request, seal request, INSERT intent |19parejas exactas; captures/header/índices/cierre igual recipe. job owner y Song coinciden, o NULL para library/import aún reservado; sólo import reserva Song. Take/Song reales cuando aplican, rights completos y AND; gates antes de efecto |
| G06 inmutabilidad | BEFORE UPDATE/DELETE salvo scope/head/intent/custody; BEFORE INSERT hijos | Contenido nunca UPDATE/DELETE; INSERT hijo aborta si existe seal root. DELETE cursores denegado; UPDATE sólo campos enumerados por CAS. No REPLACE |
| G07 audio/stems/mix | BEFORE INSERT miembros y seal audio/stems/mix | Asset Take, owner, scope, role, hash y medición reales. Audio frames/rate/duración exactos;4roles con mismo formato/canales/frames/origen0 y4controles finitos. Lineage conserva set. Inversas protegen todos los campos capturados de Asset/Take |
| G08 letra/timing | BEFORE INSERT members/bindings/lines/words/regions y seal | Counts none/single/composite, texto/hash/declaración y Song exactos. Spans medidos, tokens/slices/bindings reales, tiempos dentro de duración, confidence0..1 y NULLs de estado. Hija conserva identidad/texto/initial/audio/context; instrumental no solapa aligned. Inversas protegen letra y mapas |
| G09 cierre/sello | BEFORE INSERT seal | Root de kind enumerado existente, owner/scope y reader/family/version exactos; once schemas internos con seal_kind=NEW.kind y schema_version1, root.kind original y conjunto de campos/rows cerrado §4.11. Request/receipt mantienen D-02 sin seal_kind. Bytes canónicos completos/header/hash, counts, orden, roles y dependencias exactos; validate_seal=1. Colisión/duplicate/overwrite/extra/gap/version desconocida aborta. Root/children/capture no se alteran; reader ausente no genera sello |
| G10 CAS/transición | BEFORE INSERT revision; INSERT/UPDATE intent/head/custody/scope.song_id | §4.9: expected/predecessor/OLD exactos, incremento+1, evidencia existente de fase/ejecución correcta, cursor propio, package/cancel válidos. Bundle inicial cierra todas las FK diferidas; committed inmutable; scope import sólo materializa Song con closure/receipt final completos |
| G11 receipt/result | BEFORE INSERT receipt/artifact/result, seal y commit intent | Receipt D-02 cerrado con raw attempt/seq/terminal reales; CPU/upload sin engine ficticio. Stages reales, artifacts/paths/roles y rights completos. Final propio, XOR7sujetos, entidades/assets/hash/membership/receipt exactos. Set/import indivisibles; preview sin final success; failed Analysis sin m3_result publicado |
| G12 cancel/custody | BEFORE start/prepared/rename/commit/retry y UPDATE custody | cancel NULL salvo replay de lectura durable; custody owned y autoridad/binding/admisión actuales acreditados server. UNKNOWN bloquea efectos/serving/cleanup/release; reconciliación propia y CAS; released sin efecto pendiente. Runtime antes/después no se sustituye por hash |
| G13 inversas | BEFORE DELETE destino referenciado y UPDATE de campos capturados | EXISTS dependiente→abortar borrado/cambio de id/owner/Song/membresía/hash/path/media/bytes/text/declaration/formato/frames/map/parent capturados. Incluye Take roots/linaje y Video/Render/Shot/Asset transitivos evaluados con NEW. Song selecciones y Preset actual siguen editables; hard-delete referenciado no |
| G14 snapshot | AFTER INSERT seal/result; AFTER UPDATE intent a terminal o head | Clock global+1 por evento; Song existente no support marca dirty y generation+1. No proyecta roots privados sin seal. Library/preset global marca clock y Songs consumidores afectados; no altera capturas, Song.rev ni selecciones |

Columnas mutables exactas: scope sólo song_id en materialización; intent state/revision/active_revision_id/committed_receipt_id/committed_at/error_code; custody revision/state/binding_capture_id/custody_evidence_capture_id/reconciliation_capture_id; heads revision/active_revision_id o active_result_id. Ninguna otra tabla nueva admite UPDATE o DELETE. Edición baselinepermitida no da autoridad para violar G13. En soft-delete/declaraciónrevocada, snapshots siguen intactos pero admisión/serving autenticado revalida derechos vigentes; m3_rights_snapshot no muta.

Para checks inversos se usan los índices FK antes enumerados y los polimórficos `ix_m3_rights_snapshot_entity(entity_kind,entity_id)` y `ix_m3_request_revision_target(kind,revision_id)`; UNIQUE(kind,root_id) de seal ya cubre su búsqueda. Para operación/estado se añaden `ix_m3_request_operation(operation,subject_kind)`, `ix_m3_intent_state(state,scope_id)`, `ix_m3_intent_revision_execution(execution_id,revision)` y `ix_m3_analysis_result_lookup(take_id,audio_binding_id,method,analyzer_id,created_at)`. Estos son los únicos índices nonunique adicionales. Índice único parcial exacto `ux_m3_receipt_final(intent_id) WHERE kind IN ('publication','import','maintenance') AND outcome='succeeded'` impide dos terminales finales exitosos del mismo intent. G11 impide insertar cualquier terminal final posterior a committed. Protección transitiva G13 cubre también baseline parent tables de membresía aunque no tengan FK nuevo directo.

G14 no escribe formatos nuevos en song-v1 ni mete secretos en snapshots actuales. Proyecciónlegacy sigue reader/schemaoriginal; proyecciónM3 separada namespace privado autenticado y futura versiónD-04. snapshot_member continúa representar dependencias legacy; nuevosrootsprivados no simulan entity_songbaseline. Reconciliar despuéscommit como patrón existente; fallo proyección conservaDBdurable ydirty/retry,sin declarar publicationfallida ya committed.

### 4.13 Plan Alembic aditivo, rollback y recovery

1. **Preflight sin efectos:** comprobar head0007 del corte y head revalidado, inventario SHA baseline, FK ON y registro JSON/FTS/UDF. Obtener ventana exclusiva propia: bloquear mutaciones/dispatch/purga, drenar leases/procesos propios; UNKNOWN rechaza. Backup restaurable por API SQLite, WAL confirmado y catálogo/medios del mismo corte, con restore inerte verificado. Seam store/ext4 no liberado bloquea corte real; un harness no acredita durabilidad.
2. **Upgrade atómico:** transacción DDL writer instala las40tablas declaradas, PK/UNIQUE/CHECK/FK/índices, registra readers sin red y guards m3 forward/inverse/G14. Contar inventario exacto desde lista §4.2–4.8, verificar FK/integridad/triggers/readers antes de promover head. No ALTER/rename/rebuild Analysis/Asset/Preset/baseline; no edita0001–0007 ni amplía ADR-0074. No backfill automático de revisiones/rights/measurements/receipts/job_attempt; tablas nuevas inicialmente vacías. Registrar head sólo cuando todas las invariantes estén instaladas; fallo transaccional implica rollback completo.
3. **Lectura/adopción explícita:** histórico por reader original con bytes preservados; nueva captura sólo de fuentes reales. Binding insuficiente conserva historia y bloquea operación nueva. Primera revisión nueva de preset/timing legacy exige acción autorizada y evidencia propia; no fabrica revisión histórica. Jobs/leases restaurados permanecen inertes; leer DB restaurada no activa modelos, scheduler ni autoridad.
4. **Precondiciones de downgrade antes del primer DROP:** mantenimiento exclusivo, backup restaurable vigente, custodia reconciliada, consumidores detenidos, todas las tablas nuevas vacías (incluidas filas unsealed/failed/history), ningún medio/captura/ref M3 pendiente, runtime anterior compatible e inventario baseline exacto. Un falso rechaza antes de efectos, sin borrar filas para autorizar. No extender downgrade0006 por analogía.
5. **Downgrade vacío transaccional:** borrar sólo objetos m3, incluidos sus triggers adicionales sobre baseline, en orden inverso. Resolver ciclos nuevos con foreign_keys ON y defer_foreign_keys dentro de esa transacción; nunca FK OFF. No borrar/reinstalar guards baseline globalmente. Verificar FK/integridad/head0007 revalidado/baseline SHA y Song/FTS/snapshots sin cambios antes del commit. Un fallo revierte todo el esquema.
6. **Con datos:** ningún DROP destructivo. Deshabilitar consumidores M3 y conservar historia/readers; runtime anterior incompatible no escribe esa biblioteca. Corte previo se recupera únicamente mediante restore+activate propio D-09 exclusivo con raíz/BD juntas y rollback, preservando copia M3 original. No descartar trabajo sin acta ROOT ni reactivar jobs capturados.

Orden de creación normativo por dependencias: scope/capture/dependency; fuentes/rights/lyrics/bindings; audio/stem/mix; analysis/timing; preset/video; request e índices; intent/execution/stage/custody/revisions/evidence/receipt/artifacts; seal/result/heads. Ciclos se declaran FK deferred sin consumo antes del cierre; SQLite permite declarar tabla antes de su parent, pero todo schema queda validado antes del DML. Downgrade vacío elimina bloques inversos dentro de transacción sin DML huérfano. Inventario40 se verifica como evidencia futura; los bloques son familias, no números de migración ni estimaciones de horas.

### 4.14 Matriz de verificación futura antes de cerrar producto

Estos son **tests requeridos, no ejecutados aquí**. T-03 concreta contrato; suites/cobertura/RED corresponden a implementación liberada. Cada fila requiere positivos y negativos, SQL directo con conexión configurada y salida real en ledger ROOT. Mocks no acreditan inferencia, durabilidad FS/GPU ni aceptación humana.

| ID | Casos positivos/negativos y evidencia exigida | Cobertura |
|---|---|---|
| PD-01 | Cada columna/rango/enum/ULID/SHA/NULL/tipo; extras, duplicados JSON, bool/int, coerción, NaN/inf y cuotas D-02 en límite/+1. Once schemas internos §4.11 con seal_kind/schema_version y todos los campos/rows; seis kind root disjuntos conservados. Namespace reservado disjunto de40listas/H/header capture. Casos FIX1 completos/negativos por familia, sin reparar representación anterior. Reader/version desconocido rechaza sin default | SQL/reader |
| PD-02 | Migrar DB0007 con historia real; inventario exacto de tablas/guards/FK. Bytes/IDs/UNIQUE Analysis intactos; analyzer_version fuera. Asset job/analysis/import/backup rechaza; DTO/schema M1 igual | migración/legacy |
| PD-03 | Cada FK simple/compuesta; owner/Song cruzado, global autorizado, reserva Song sólo import. Cambios inversos transitivos y hard-delete abortan; current master/letra cambia sin retarget | CA02/SQL |
| PD-04 | Captura/seal DAG, orden contiguo y armado parcial invisible. Cada familia interna verifica root+rows+seal_kind/schema_version→canónico→SHA/header→G09 y kind SQL intacto; hash sin seal_kind, bytes distintos de SQL, colisión/overwrite/duplicate/gap/extra/version incorrecta rechazan. Sello incompleto, UPDATE/DELETE contenido o INSERT posterior de hijo rechazan por SQL; dos sealers sólo uno gana | SQL/concurrencia |
| PD-05 |4stems y roles/hash/rate/channels/frames/offset0 exactos;3/5roles, retag y bytes alterados rechazan. Mute+solo, varios solos, solo muteado, silencio, gain0/finita/NaN; reload mismos controles y SHA | CA08/E2E08 |
| PD-06 | Single histórico y composite real; letra actual cambia sin afectar historia. Plan puro no mide; mix final versus master antiguo, duración exacta, conversión medida y canción>180s completa; sin LyricsVersion sintética | CA18/E2E18 |
| PD-07 | Repetidas/omitidas/uncertain/instrumental/silencio/líneas largas; tokens/slices/bindings/tiempos/confidence válidos. Hija cambia tiempos/estado sin audio/texto/initial; retokenización como corrección rechaza | CA20/E2E20 |
| PD-08 |5métodos independientes y outcomes honestos; sections textual no cuenta medido. Analysis original/hash intacto y nuevos results sin UPDATE ni analyzer ficticio | CA48/SQL |
| PD-09 | Preset create/edit sella nueva revisión/CAS y valores/refs; soft-delete no retargetea, hard-delete referenciado rechaza y capacidad no verificada bloquea. Video rev7 persiste al editar a rev8 | CA34/E2E34 |
| PD-10 |19parejas/7sujetos y slots XOR/roles completos. result.kind conserva7sujetos con seal_kind=result; source/rights/lyrics/audio/preset preservan sus propios enums. Request/recipe/receipt D-02 y wrappers conservan schema; seal_kind extra rechaza. Original export target NULL; upload sin model/seed, CPU sin ganador, biblioteca sin Take, reserva import y closure atómico | CA02/48 |
| PD-11 | Reserved revision1 con evidencia existente antes de efecto sin success ficticio; start después de reserva durable. Raw no publicación, stages/post propios, package/rename/final exactos; evidence ausente/fase errónea rechaza | fases/SQL |
| PD-12 | Dos writers con mismo expected cursor/result_key: un CAS gana y el otro revierte su revisión. Incremento+1/overflow, heads mix/timing/preset/analysis; committed inmutable y ninguna dedup por hash | concurrencia |
| PD-13 | Cancel antes de send/raw/prepare/rename versus commit; commit previo gana. Lost ACK raw/final, replay exacto sin doble entidad/receipt/regeneración; retry ordinal nuevo y misma captura | races/replay |
| PD-14 | Crash en cada frontera, disco lleno/flush/close UNKNOWN. Custodia incierta bloquea efectos/publicación/serving/cleanup/release; reconciliar antes de retry. Archivo ajeno de igual hash/path rechaza | recovery |
| PD-15 | Artifacts/roles completos, Analysis sin medio/Asset ficticio y preview expirado sin durable commit. Portable sin autoridad activa e import closure indivisible; fallo revierte transacción | publicación |
| PD-16 | Rights/AND de inputs/padres/tools/model realmente usado; false propaga, consentimiento ausente falla, CPU no atribuye modelo padre. DTO/log/legacy/portable sin secretos/prompts/fotos/PID/token/path privado | CA48/privacy |
| PD-17 | Registro en ORM/worker/Alembic/import/restore/mantenimiento/tests; sin UDF aborta captura/seal, sin FK/guards falla conexión; SQL directo tampoco evita reglas y baseline guards intactos. Reader cerrado por11familias, captura/header/version y G09 exactos; unknown/oldcollision nunca selecciona fallback. Esquemas externos/históricos mantienen sus positivos originales y rechazan seal_kind extra | SQL/integración |
| PD-18 | Downgrade vacío conserva baseline; cualquier fila unsealed/failed/history/ref/custodia pendiente bloquea antes de DROP. Fallo DDL revierte todo; con datos conserva o restore completo inerte | rollback |
| PD-19 | Restore biblioteca nueva con integridad/FK/FTS/medios/reproducción y jobs inertes; activación raíz/DB junta y rollback D-09. Head/reader ausente bloquea, documentación no cuenta prueba real | mantenimiento |
| PD-20 | Clock/dirty ante nuevo sello/head/terminal y recovery de snapshot posterior a commit; no Song.rev ni secretos/rewrite. Library sin Song fake; support sólo mutación baseline autorizada de import/promoción | proyección |

E2E-02/08/18/20/34 y M-48 siguen íntegros. La matriz añade SQL/migration/races/rollback/legacy y mantiene reproducción real, inspección independiente y aceptación humana. Cobertura mínima80% changed-only y TDD del plugin aplican a implementación futura, con RED dependiente después de ratificar D-03/D-04 y sus gates. Aquí no se ejecutan SQL/DB/tests/harness.

## 5. Impacto en módulos y ficheros

| Ruta real del corte | Impacto futuro de PD-O1 / PD-O2 | Estado en esta entrega |
|---|---|---|
| `apps/server/app/models/__init__.py` | Entidades adicionales tipadas / filas documentales con claves relacionales; baseline preservado | Sólo lectura |
| `apps/server/app/migrations/versions/` | Nueva revisión hija de0007, DDL aditivo y downgrade condicionado | Sólo lectura; número futuro no reservado |
| `apps/server/app/migrations/cpu_publication_invariants.py` | Patrón existente de guards SQL y validación directa; M1 conserva contrato | Sólo lectura; no reutilización de autoridad ficticia |
| `apps/server/app/migrations/initial_invariants.py`, `fix1_invariants.py`, `fix2_invariants.py`, `fix3_invariants.py` | Modelos de owner/subject/DAG/root/inversas; nuevos guards separados, sin editar historial | Sólo lectura |
| `apps/server/app/queue/chains.py`, `dispatcher.py` | Persistencia M3 sobre cola existente; retry/cancel por resultado, sin nuevo runner | Sólo lectura |
| `apps/server/app/worker/contracts.py`, `planning.py`, `execution.py`, `publications.py` | Readers legacy M1 intactos; namespace M3 separado, fases/recibos propios | Sólo lectura |
| `apps/server/app/creative/recipes.py`, `composition.py` | Referencias a capturas M2 históricas y planes puros; no habilitan runtime por hash | Sólo lectura |
| `apps/server/app/snapshots.py`, `backup.py` | Proyección adicional discriminada y recovery inerte; formatos/catálogos bajo D-04/08/09 | Sólo lectura |
| `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-data-contract.md` | Destino canónico que ROOT mapeará desde el candidato elegido | No escrito por actor |
| `docs/arquitectura/datos.md` | Apéndice aditivo que ROOT extraerá después de revisión/QA; prefijo conservado | Sólo lectura |
| `docs/roadmap/2026-10-11-m3-production-data/design.md` | Opciones privadas de esta iniciativa auxiliar del snapshot | Único fichero escrito |

### Migración seleccionada y revalidación del corte

Upgrade futuro exige ventana exclusiva, mutadores/dispatch/purga detenidos y custodia reconciliada. UNKNOWN impide iniciar el corte. Backup SQLite incluye WAL confirmado y restauración verificada; no se copia un VHDX activo.

La revisión añade las40tablas, índices, checks, FK diferidas y triggers especificados en §4. No reconstruye Analysis/Asset/Preset ni edita0001–0007. Esta segunda pasada cierra estructura, validación de readers y dependencias de instalación.

Las filas históricas conservan IDs/valores/SHA. No se inventan revisions, mediciones, rights o resultados para backfill. Las vistas legacy y nuevas despachan separadamente. Un histórico sin binding suficiente se conserva legible y bloquea la operación nueva que necesite ese binding.

Downgrade sólo procede antes de datos M3 y sin referencias/custodia activa, con guards previos a efectos. Datos existentes impiden DROP; la recuperación conserva esquema e historia o restaura un corte completo bajo mantenimiento. No elimina contenido para hacer caber un reader anterior ni reactiva jobs.

El head0007 es hecho **estático del snapshot**, no promesa del head futuro. ROOT comunica actividad M2/T-05 en snapshot independiente: contrato CPU de las3tablas de ADR-0074, sin DDL/runtime al comunicarlo; también informa adopción/publicación de K2 en `755b476` y apéndices M1 posteriores al corte. Ese overlay es contexto recibido de ROOT, no nueva fuente SHA de este actor ni acreditación runtime. Antes de liberar implementación M3 se revalida head real, grafo Alembic, contratos M2 CPU, K1/K2, guards de plataforma y releases D-12 por operación/versión/SHA. Si el head avanzó, una revisión M3 nueva parte de ese head verificado por handoff explícito; no se adopta número0008 ni se crea branch/mergehead por suposición. Incompatibilidad requiere nueva decisión antes del RED, sin alterar el inventario99 histórico ni aplicar ADR-0074 a Analysis/Asset/Preset.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Modificar Analysis para esquivar su UNIQUE | Media | Alto | Evidencia original intacta; resultados nuevos en familia aditiva con identity propia |
| `result_evidence_ref` parece exigir resultado en reserved | Alta sin fases | Alto | Evidencia privada reserved existente; revisiones posteriores execution/prepared/commit, nunca éxito anticipado |
| Revisión de contenido confundida con cursor CAS | Media | Alto | Enumerar ambos números y fase; CAS compara cursor/estado/identidad completos |
| Mover stem/take/letra/preset referenciado de propietario o canción | Media | Alto | Guards de inserción y comprobación inversa; impedir mutación de identidad/binding referenciado |
| Dos writers ganan el mismo result_key | Media | Alto | UNIQUE propia de resultado reservado y CAS en transacción; perdedor sin efecto nuevo |
| Cancel entra entre prepare y commit | Media | Alto | CAS y cancel observado antes commit; commit durable ya acreditado prevalece sobre cancel tardío |
| ACK perdido provoca regeneración/doble publicación | Media | Alto | Replay del receipt y resultado propios, recuperación por intención, no hash/path aislados |
| UNKNOWN se usa como permiso para limpieza/retry | Media | Alto | Custodia separada y bloqueante hasta reconciliación real |
| Composite parece acreditado por un plan CPU puro | Media | Alto | Binding medido propio posterior y hash de audio/duración; validación pura no concede autoridad |
| Rollback destruye revisiones nuevas o reanima jobs | Media | Alto | Guard antes de efectos; preservar datos/historia; restore inerte y activación separada |
| Reader de perfiles sin D-05–09 acepta JSON libre | Media | Alto | Refs/reader/version exactos, schema ratificado obligatorio antes ejecución |
| Discriminante JSON del sello pisa kind de fuente/rights/letra/audio/preset/resultado | Confirmado en fuente previa no adoptada | Alto | FIX1: seal_kind reservado, kind SQL intacto;11schemas con campos/rows y hashes completos, namespace disjunto, G02/G09 cerrados y casos PD-01/04/10/17 |

## 7. Preguntas abiertas

No quedan alternativas internas de D-03 pendientes: ROOT eligió PD-O1 y esta segunda pasada fija sus columnas, referencias, guards, fases, tipos y rollback. La adopción del candidato exige revisión y QA documental frescas; el estado T-03 y las métricas siguen exclusivamente bajo ROOT.

Quedan gates externos de D-04/05/06/07/08/09/11, T14 temporal y componentes D-12. §4.11 identifica exactamente el reader y la operación bloqueada que corresponden a cada uno. No se difiere allí una decisión SQL/CAS/timing/preset interna de D-03. El contrato no los aprueba ni reduce el alcance M3.

### Apéndice candidato para datos.md — extracción exclusiva ROOT

ROOT extraerá únicamente el texto entre los delimitadores `BEGIN ROOT-DATA-APPENDIX` y `END ROOT-DATA-APPENDIX` y lo añadirá a `docs/arquitectura/datos.md` sin reescribir su prefijo. Los marcadores delimitan evidencia de entrega, no comentarios guía. El contrato completo se mapeará de este diseño a `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-data-contract.md`; ambos destinos se crean/adoptan juntos tras revisión/QA y se comprueban sus enlaces allí.

<!-- BEGIN ROOT-DATA-APPENDIX -->

## Apéndice normativo M3 — Persistencia tipada D-03 (propuesta seleccionada)

PD-O1 mantiene el baseline y añade40tablas propias `m3_*`. Su especificación de columnas, tipos, nullability, PK/UNIQUE/FK/checks, índices, guards, readers, fases y rollback está en §4 del contrato `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-data-contract.md`. Fuente seleccionada bajo delegación ROOT, pendiente revisión/QA/adopción; no DDL ejecutado ni función M3 acreditada.

| Familia aditiva | Tablas y obligación |
|---|---|
| Scope/capturas | m3_scope, m3_capture, m3_capture_dependency, m3_source_snapshot, m3_rights_snapshot. Song existente o reserva import propia; biblioteca binding propio sin Song/Take ficticios. Bytes/reader/hash y dependencias cerrados; derechos verificables |
| Letra/audio | m3_lyrics_context, m3_lyrics_member, m3_lyrics_binding, m3_audio_binding. Historia none/single/composite y audio efectivo medido: hash/rate/channels/frames/duración exacta; mapa puro no acredita salida |
| Stems/mix | m3_stem_set, m3_stem_member, m3_mix_revision, m3_mix_stem, m3_mix_head.4roles completos y formato/origen común; revisiones inmutables; mute domina solo, cualquier solo filtra no solos; ganancias lineales finitas; bytes de master/stems intactos |
| Analysis/timing | m3_analysis_result, m3_analysis_head, m3_timing_revision, m3_timing_line, m3_timing_word, m3_timing_region, m3_timing_head. Resultados por método/outcome y correcciones con tokens/bindings/initial/audio originales, tiempos dentro de duración e incertidumbre/missing/instrumental honestos |
| Preset/video | m3_preset_revision, m3_preset_source, m3_preset_head, m3_video_revision. Edición sella revisión nueva y cada uso congela valores/refs; timeline rev/hash conserva autoridad histórica |
| Request | m3_request, m3_request_source, m3_request_parent, m3_request_rights, m3_request_revision. Índices exactos de recipe D-02, sin sidecar/doble autoridad ni JSON libre;19parejas/7sujetos |
| Ejecución/autoridad | m3_intent, m3_execution, m3_execution_stage, m3_custody, m3_intent_revision, m3_phase_evidence. Reserva revision1 y evidencia existente antes de efectos; CAS de identidad/estado/revisión/cursor; custodia separada; UNKNOWN bloquea efectos y serving |
| Recibos/publicación | m3_receipt, m3_receipt_artifact, m3_seal, m3_result. Raw/CPU/upload y final publication/import/maintenance discriminados; cierre sellado, roles exactos y entidad/resultado/receipt en mismo commit SQLite; no FS+SQLite atomicidad inventada |

`analysis` sigue UNIQUE(take_id,kind,analyzer_id), con analyzer_version fuera de la clave. Ninguna corrección ni método nuevo reescribe fila/data original. Asset.subject_type sigue take/artwork/shot_version/render/export/character/lora/cli_run; no job/analysis/import/backup. Preview temporal sigue privado del job; import/backup tienen capturas/recibos propios, no Asset ni entidad ficticia.

Todas las FK nuevas son diferidas con NO ACTION; cada referencia tiene índices y validación forward/inverse de owner y pertenencia transitiva. Content roots/children/capturas son append-only; seal único impide añadir children posteriores. Head/intent/custody son los únicos cursores mutables por CAS; scope sólo materializa Song reservada en commit import íntegro. Rights, tokens/texto histórico, audio y receipts sellados no se sobrescriben. Baseline current master/letra/portada y preset actual pueden cambiar sin retargetear historia.

FIX1 B01 fija para las11familias internas source/rights/lyrics/audio/stems/mix/analysis/timing/preset/video/result el conjunto exacto de todos los campos root/H, NULLs, rows hijas tipadas y ordenadas, más JSON reservado `seal_kind=m3_seal.kind` y `schema_version=1`. Root.kind se conserva cuando existe; nunca se añade a roots sin esa columna. Namespace reservado cerrado seal_kind/schema_version/members/bindings/stems/lines/words/regions/sources, con arrays sólo por familia §4.11 del contrato, disjunto de las40listas de columnas/H/header capture. No extras, gaps, claves duplicadas ni overwrite. Request/recipe/receipt D-02, wrappers, perfiles, fases e históricos mantienen schemas originales y no reciben seal_kind. G02/G09 validan reader/family/version, bytes canónicos completos y SHA del payload con ambos discriminantes cuando aplican, comparando SQL sin alterar kind. Hashes originales de fuente/evidencia conservan su dominio; no hash autorreferente ni alias/default de la proyección ambigua anterior no adoptada. No renombra columnas SQL ni crea versión histórica. Casos positivos/negativos FIX1 por todas las familias quedan en PD-01/04/10/17.

Estados intent reserved/prepared/committed/failed/cancelled y fases reserved/executing/executed/prepared/renamed/committed/failed/cancelled tienen evidencia existente propia. `result_evidence_ref` no es nullable: reserved usa reservation1 sin receipt succeeded, execution usa hechos reales y sólo commit usa terminal final. Cancel previo impide commit; commit durable prevalece ante cancel tardío/ACK perdido con replay exacto. Retry explícito conserva captura/result_key y añade execution ordinal/revisión, después de reconciliar custodia; UNKNOWN nunca autoriza limpieza ni nueva ejecución.

Migración aditiva sobre head revalidado (snapshot0007), sin editar0001–0007 ni ampliar la excepción ADR-0074 más allá de take/publication_intent/publication_intent_revision. Sin backfill ficticio de revisiones, mediciones, rights o ganadores. Downgrade sólo si todas las tablas M3 están vacías y no hay custodia/refs/medios pendientes, tras comprobación anterior a cualquier DROP. Con datos se conserva historia/readers o se restaura corte completo en biblioteca nueva, jobs/leases inertes y activación raíz/BD conjunta bajo D-09.

Readers cerrados D-03 se registran en **todas** las conexiones antes de DML; ausencia, versión desconocida o gate externo faltante falla cerrada. D-04 fija paquetes/readers de publicación; D-05/06/07 perfiles y mediciones; D-08 catálogo/cierre/importmap; D-09 cut/binding/restore/rollback. Esos gates bloquean consumo concreto hasta ratificación; no completan con defaults ni alteran históricos v1/v2, schema/DTO M1 o /v1. Matriz PD-01..PD-20 del contrato exige pruebas futuras SQL/migration/races/rollback/legacy/privacy y conserva E2E/M-48 del plan.

<!-- END ROOT-DATA-APPENDIX -->

### ADR candidato sin número — extracción exclusiva ROOT

ROOT reservará ID/slug/ruta sólo después de revisión. Extraer texto entre `BEGIN ROOT-ADR-CANDIDATE` y `END ROOT-ADR-CANDIDATE`; no se crea ADR/índice público en este turno. Los paths canónicos son destinos previstos; el índice y enlaces se completarán al adoptar, no se atribuye número pendiente a un ADR vigente.

<!-- BEGIN ROOT-ADR-CANDIDATE -->

---
titulo: Persistencia aditiva tipada y revisiones inmutables de producción
estado: propuesta
fecha: 2026-10-11
decision: D-03
opcion_elegida: PD-O1
autoridad_de_eleccion: ROOT bajo delegación vigente; 2026-10-11T19:28:24.366015+00:00
namespace: candidato sin número; pendiente revisión/QA/adopción ROOT
---

# ADR candidato — persistencia de producción y revisiones

## Contexto

ADR-0080 fija derivados sobre cola job/job_dependency y ADR-0082 fija ProductionRequest1/Recipe1 privados,19parejas/7sujetos, CAS y recibos discriminados. El baseline Analysis tiene UNIQUE(take_id,kind,analyzer_id), analyzer_version fuera; Asset no admite job/analysis/import/backup. Los snapshots/planes M1/M2 y manifiestos v1/v2 conservan bytes/semántica originales. ADR-0074 limita sus reconstrucciones a3tablas CPU, sin permiso análogo para Analysis/Asset/Preset.

Se compararon PD-O1 y PD-O2 en la primera pasada preservada SHA428b5cecdbde017ce5616a7c139e4cec6a81674e177e58011398deb668a91cd4. ROOT eligió PD-O1 mediante choice-root.receipt.json SHAc0c651cee5b4a0eaa58fa02ac3a9a081a6dad49cfe3dbd6cd6a44b7e54495ea1 bajo delegación vigente. No se atribuye ratificación personal de cada fila al propietario.

## Decisión propuesta

Añadir40tablas m3_* con relaciones tipadas, capturas canónicas privadas cerradas, roots/children append-only y sello único antes de consumo. Guards SQL directos forward/inverse fijan pertenencia, estados, referencias, DAG, revisiones y CAS. Results/receipts tienen siete sujetos independientes; preview sigue temporal, import/backup mantienen scope/autoridad propia sin Take/Asset fake. El contrato completo se adoptará en `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-data-contract.md` y un apéndice aditivo en `docs/arquitectura/datos.md`.

El FIX1 documental B01 seleccionado por ROOT reserva `seal_kind` en los11schemas internos nuevos: su valor es m3_seal.kind, mientras root.kind conserva íntegro su enum SQL. El payload exacto incluye root/H/NULLs/rows ordenadas, seal_kind y schema_version1, con namespace reservado disjunto de las40tablas/header capture, parsing sin duplicates, extras, gaps, overwrite ni fallback. G02/G09 comparan reader/family/version, SQL, bytes canónicos y hash del payload completo; hashes de fuente/evidencia y refs históricas conservan su dominio. Se aplica a todas las familias internas, no sólo audio; request/recipe/receipt D-02 y otros schemas originales/históricos no reciben seal_kind. La fuente anterior no adoptada sigue preservada: no versión legacy fabricada ni renombre SQL, reescritura histórica o nueva alternativa a PD-O1.

MixRevision conserva4stems/controles y no modifica audio. LyricsTimingRevision conserva resultado inicial, tokens/texto/single-composite/bindings/audio medido/hash/duración, con tiempos y procedencia de corrección nuevos. PresetRevision congela valores y refs efectivas de cada edición/uso. Resultados por método nuevos viven fuera del UNIQUE Analysis original, sin overwrite ni analyzer ficticio.

Reservation revision1 se confirma con evidencia reserved existente antes de efectos; no requiere ni inventa receipt succeeded. Nuevas fases tienen evidence propia y CAS del cursor/estado/identidad completos. Terminales raw/CPU/upload no son publicación; entidades/results/receipt final son commit SQLite indivisible, FS tiene recovery separado. Commit durable prevalece ante cancel tardío/ACK perdido; UNKNOWN bloquea efectos/serving/cleanup/liberación hasta reconciliación.

Upgrade es aditivo tras head0007 del corte revalidado y ventana propia exclusiva; no reconstruye Analysis/Asset/Preset ni modifica0001–0007. Sin backfill ficticio. Downgrade vacío guardado antes de efectos; con datos conserva historia/readers o restaura corte completo inerte mediante activación D-09. Readers de perfiles/formatos futuros son gates cerrados, no catch-all ni defaults. /v1, DTO/schema M1, histórico y ADR-0074 permanecen intactos.

## Alternativas descartadas

- PD-O2: documentos tipados versionados con índices y lectores SQL. Viable, menor DDL y coste relativo M, pero más dependencia de registro por conexión y duplicación de identidad en columnas/documento. PD-O1 cuesta L y más DDL; aporta relaciones explícitas que responden mejor a pertenencia, bindings y fases.
- Modificar UNIQUE/data de Analysis, añadir Asset.subject_type job/analysis/import/backup, fabricar Take/JobAttempt/seed para sujetos CPU/biblioteca o sesión agregada: contradicen baseline/ADR-0074/0080/0082 y no se adoptan.

## Consecuencias y límites

Aumenta el número de tablas y guards; la implementación debe expandir íntegra la matriz, probar SQL directo, migraciones, readers por conexión, race/cancel/replay y rollback. Todas las fuentes/historia se conservan, con head separado de revisión inmutable. Las conexiones sin reader/guards fallan cerradas; privilegios administrativos de SQLite no se confunden con el boundary del server autenticado.

La fuente sigue propuesta seleccionada hasta revisión/QA/adopción ROOT. No hay DDL/código/DB/runtime ejecutado ni T-03 cerrada por esta entrega; funciones M3 implementadas0. D-04/05/06/07/08/09/11 y releases de plataforma D-12 permanecen gates propios. El inventario99 de fuentes es snapshot readonly; cualquier overlay K2/M2 y head futuro se revalida al handoff del implementador.

## Verificación requerida

PD-01..PD-20 en el contrato, criterios CA-02/08/18/20/34/48 y E2E-02/08/18/20/34/M-48 del plan. ROOT reserva ADR, completa índice/enlaces y adopta junto a contrato/apéndice sólo tras revisión/QA. El sello/hash documental no certifica mediciones, derechos, custodia, inferencia ni conformidad audiovisual.

<!-- END ROOT-ADR-CANDIDATE -->

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-11 | Borrador con dos opciones aditivas, recomendación PD-O1 y selección pendiente de ROOT |
| 2026-10-11 | ROOT selecciona PD-O1; segunda pasada cierra contrato D-03,40tablas/14familias de guards/20verificaciones futuras y candidatos de apéndice/ADR delimitados; adopción pendiente |
| 2026-10-11 | FIX1 B01 seleccionado ROOT separa seal_kind reservado de root.kind; cierra11schemas, namespace/hash/reader/G09 y casos futuros PD-01/04/10/17; apéndice/ADR candidatos coherentes, sin código ni adopción |

### Evidencia de reanudación — primera pasada

Reanudación del actor arquitecto tras interrupción del anterior. Se leyeron `task-brief.md`, `release-root.receipt.json` y las 99 fuentes UTF-8 del snapshot: 3110068 bytes, 53715 líneas leídas; cálculo SHA-256 exclusivamente readonly. Salida real de comprobación: `sources=99; mismatches=0; readonly_sources=true`. La comparación no selecciona una opción ni cierra T-03; sólo corrige la referencia de línea de Preset y conserva las dos alternativas.

Se comprobó expresamente ADR-0082 aceptada y su acta de adopción, las 19 parejas y siete sujetos, el UNIQUE histórico de Analysis y el enum cerrado de Asset. No se ejecutaron SQL, importaciones ORM, migraciones, tests, modelos, GPU, servicios, Docker, WSL ni instalaciones. No se tocaron canon, ledger, Git ni medidor de uso. El modelo/tier del frontmatter describe el recibo ROOT y no atribuye ejecución a un modelo distinto.

Estado de **aquella primera pasada histórica**: selección pendiente, ADR pendiente y borrador. Queda preservada completa por ROOT. El estado vigente de esta segunda pasada es PD-O1 seleccionada y fuente propuesta pendiente revisión/QA/adopción; no estado cerrado de T-03.

### Evidencia final de segunda pasada y cese

Lectura documental del candidato de `production-data-contract.md` permitido en este `design.md`: matriz SQL/ownership/CAS y concurrencia en §4.2–4.12; migración aditiva/rollback con guard previo a efectos en §4.13; prohibición de reescribir Analysis original en §4.5. Apéndice de datos y ADR candidato delimitados en §7. La Verificación de T-03 se prepara sobre este candidato mapeable; ROOT comprobará el archivo canónico al adoptar. No se declara función, T-03 ni hito cerrado por esta entrega.

Salida real de inspección readonly final, anterior únicamente a añadir este bloque de evidencia:

`sources=99; mismatches=0; tables=40; unique_tables=40; guards=14; future_test_groups=20; operation_subject_pairs=19; numbered_sections=7; placeholders=0; extraction_markers=4`

SHA options preservadas `428b5cecdbde017ce5616a7c139e4cec6a81674e177e58011398deb668a91cd4`; SHA choice ROOT `c0c651cee5b4a0eaa58fa02ac3a9a081a6dad49cfe3dbd6cd6a44b7e54495ea1`. Es inspección estructural/documental, no ejecución de PD-01..PD-20, SQL, DB, ORM, Alembic, harness, inferencia ni plataforma. Todos siguen pendientes en implementación futura. Única escritura: este design.md; ninguna fuente del inventario99 modificada. Uso real null, sin medidor del actor. La fuente se entrega congelada a ROOT y el actor cesa antes de revisión fresca/QA.

### Evidencia FIX1 B01 y cese documental

Actor fresco FIX1 lee el brief, recibo de release y revisión previa completa A29/B25. Sólo escribe `snapshot/docs/roadmap/2026-10-11-m3-production-data-fix1/design.md` en el namespace privado `production-data-t03-contract-fix1-20261011`; otras fuentes/actores permanecen intactos. Fuente original readonly comprobada SHA `f982b1bd9c3fc181034911902c9b39dc29943266be8b56941c5ac4b9b6b56d46`,105751bytes. Elección/opciones y toda evidencia histórica de las pasadas anteriores se conservan; PD-O1 no se reabre.

Verificación real por lectura/inspección estática: matriz SQL/ownership/CAS y concurrencia §4.2–4.12, migración reversible/rollback §4.13 y prohibición de reescribir Analysis §4.5 están presentes. Las40filas de definición SQL son exactamente iguales a las de la fuente original; el prefijo completo hasta §4.10 es idéntico. La revisión de campos por nombre completo (incluido sha256) comprueba los11fieldsets contra sus columnas SQL y expande H en todas las40tablas; no ejecuta un serializer ni un test de producto.

Salida real anterior únicamente a añadir este bloque: `readonly_sources=101; mismatches=0; tables=40; unchanged_table_rows=true; expanded_column_occurrences=384; reserved_collisions=0; internal_fieldsets=11; fieldset_errors=0; guards=14; future_test_groups=20; operation_subject_pairs=19; numbered_sections=7; placeholders=0; extraction_markers=4; original_prefix_through_4_10_unchanged=true; old_ambiguous_rule_matches=0`.

| Hallazgo confirmado | Cambio documental verificable | Estado de esta entrega |
|---|---|---|
| B01 Important, colisión root.kind/seal.kind | §4.11 reserva seal_kind y conserva root.kind;11fieldsets/rows completos,6dominios disjuntos y5roots sin kind; namespace/hash/version/G02/G09 cerrados, positivos/negativos y PD-01/04/10/17, apéndice/ADR candidatos coherentes | Corregido documentalmente; pendiente revisión fresca y QA ROOT |

TDD n/a: prosa documental; no se han escrito ni ejecutado tests/harness/SQL/ORM/DB/migraciones, modelos/GPU, servicios, Docker/WSL, instalaciones ni código. No escritura canónica, ledger, Git, medidores ni adopción. No T-03/D-03 ni hito cerrado; no función M3 acreditada. ROOT conserva la extracción/adopción de ambos candidatos y la decisión sobre el siguiente gate. Este actor entrega su única fuente congelada y cesa; SHA/tamaño final se devuelven a ROOT fuera de los bytes de esa misma fuente.
