---
design: m2-t02-private-recipe-contract
titulo: Contrato privado de captura de recetas musicales y ediciones CPU
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: spec.md
evaluacion: n/a (ADR-0001)
plan: improvement-plan.md
adr: ../../decisiones/ADR-0077-envelope-privado-de-recetas-creativas.md
opcion_elegida: O1
validacion: ROOT bajo delegación del propietario, 2026-10-11; contrato ratificado tras revisión A+B intento 2 y QA documental 18/18.
generacion:
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  nota: Sin marcador del actor; ROOT conserva el único marcador m2/T02-recetas-privadas. Prosa, sin medida de consumo real.
---

# Diseño — contrato privado M2/T02

> Spec aprobada, plan en progreso. Propuesta privada para revisar antes del RED. O1 elegida por ROOT bajo delegación; el contrato detallado aún requiere su revisión. No representa aceptación de T02 ni M2.

| Campo | Valor |
|---|---|
| Estado del enfoque | Aprobado por ROOT el 2026-10-11 |
| Opción elegida | O1 — envelope exclusivo y proyección explícita |
| Contrato detallado | Propuesta para revisión ROOT; no integrado |
| Validación del propietario | Delegación al orquestador; no lectura ni elección personal de este documento |

## 1. Contexto y restricciones

ADR-0073 fija receta privada en `job.request`. ADR-0074 conserva inferencia M1 y prohíbe fingir modelo, semilla o intento de engine para CPU. Ambos permanecen aceptados.

T02 crea solamente `creative/recipes.py`, su exportación, tests puros y el documento de arquitectura. No modifica ORM, SQL, cola, worker, contratos públicos ni schemas generados. T03 concreta construcción por muestras; T04 exporta schema y fixtures; T06 integra admisión; T07 integra autoridad/publicación CPU.

`Job.request` es JSON de dominio. `JobAttempt.engine_request` conserva el `JobRequest` efectivo. `resolver.py` rechaza cualquier clave externa a `params/inputs/seed/n_outputs/timeout_s/mode/required_features`. Por tanto, el envelope nuevo necesita dispatch posterior explícito; no puede enviarse al resolver M1 intacto.

`PostPlan.version=1` y su handler `post.audio` identifican post de inferencia. Que ese post use CPU no cambia el origen musical. `private_context.py` conserva su propio recibo `version=1`, distinto del namespace de receta.

Las cuatro rutas de producto declaradas por T02 no existen en el preimage del actor. Se documentan como destinos nuevos. Los módulos M1 citados aquí sí existen.

## 2. Opciones (3)

### O1 — Envelope exclusivo versionado

Los jobs creativos nuevos guardan una única receta sellada dentro de un envelope cerrado. La integración posterior deriva parámetros y referencias desde ella. El reader distingue explícitamente estos jobs de M1.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: un reader y una proyección nueva explícita |
| Riesgo | Medio: requiere dispatch antes de resolver; no tiene doble fuente de parámetros |
| Coste relativo | M |
| Reversibilidad | Alta: lector por versión, históricos intactos |

### O2 — Sidecar dentro de petición M1

La petición conserva `params/inputs/seed` y añade una clave `creative_recipe`. Facilita adaptar consumidores existentes, pero duplica la autoridad de datos.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: validar igualdad y mantener dos formas |
| Riesgo | Alto: la receta y los parámetros ejecutados pueden divergir |
| Coste relativo | S |
| Reversibilidad | Media: consumidores podrían depender de cualquiera de las dos copias |

### O3 — Registro de receta separado

Una tabla o registro durable contiene la receta. `job.request` guarda su referencia. Exige nueva persistencia y reconciliación; excede T02 y la captura decidida por ADR-0073.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: nueva relación, readers y reconciliación |
| Riesgo | Alto: introduce una segunda autoridad persistente |
| Coste relativo | L |
| Reversibilidad | Media: las referencias persistidas obligan a conservar el registro |

## 3. Criterios de decisión

1. Preservar bytes, hashes, ausencias y significado de M1.
2. Una única autoridad para parámetros, letras, fuentes y linaje nuevos.
3. Captura pura implementable antes de modificar admisión o BD.
4. Rechazar versiones desconocidas antes de ejecutar o reinterpretar.
5. CPU declara herramientas; las identidades musicales de los padres siguen siendo antecedentes.

## 4. Recomendación · opción elegida y por qué

**O1 elegida por ROOT bajo delegación el 2026-10-11.** Cumple los cinco criterios. O2 duplica autoridad. O3 añade persistencia fuera de alcance. Esta elección no reabre O2 global de ADR-0073 ni O1 de representación CPU de ADR-0074.

### 4.1 Envelope y límites exactos

Todos los nombres de tipos siguientes son nuevos, privados del server y propuestos para T02. Los símbolos de M1 mantienen sus firmas.

`CreativeRequestV1` tiene exactamente cuatro claves obligatorias:

```text
kind: Literal["creative_recipe"]
schema_version: Literal[1]
recipe: CreativeRecipeV1
recipe_sha256: SHA256
```

`schema_version` debe ser `type(value) is int`; bool, string, float y versiones distintas fallan. La receta no repite versión ni SHA. `recipe_sha256` es SHA-256 de sus bytes canónicos UTF-8. El SHA del envelope completo es diferente, y no sustituye ese SHA.

La unidad ofrece `capture_request()` y devuelve el envelope; el caller posterior lo guarda entero en `Job.request`. T02 no abre sesiones ni escribe jobs. No agrega campos a peticiones M1 ya emitidas.

Límites de nuevas recetas: 1 MiB UTF-8 canónico; profundidad JSON máxima 20; máximo 256 elementos por colección JSON. Strings generales hasta 8192 caracteres; letra hasta 32768 y estilo hasta 4000. Descriptor y pin permanecen sujetos al límite total. No truncar: rechazo tipado.

Precedencia: los límites específicos sustituyen al general para `lyrics.versions[].text`, `executor.params.lyrics`, `operation.basis.request.params.lyrics` (32768), y los campos `params.style` de selection/basis (4000). Los campos de identidad tienen su límite menor explícito. Los demás valores str originales mantienen 8192. El texto backing de FrozenJSON/FrozenDescriptor no es una string original del documento: se valida su JSON antes de congelar y sólo se le aplica el límite total 1MiB, nunca 8192. No iterar por el backing canónico como si fuera un nuevo valor textual. La letra con más de8192 y hasta32768 caracteres es válida si cumple el resto de sus reglas/schema.

### 4.2 Tipos escalares y serialización

| Tipo | Regla |
|---|---|
| ULID | `str`, patrón `^[0-7][0-9A-HJKMNP-TV-Z]{25}$`; no coerción ni minúsculas |
| SHA256 | `str`, 64 hex minúsculas; no prefijo |
| ImageDigest | `sha256:` más SHA256, cuando corresponde |
| Seed | Nuevo destino: int no bool, 0..2**64-1 |
| HistoricalSeed | Antecedente: int no bool, >=0; respeta el contrato M1, sin imponer retrospectivamente el límite nuevo |
| Seconds | int o float no bool, finito; captura normaliza explícitamente a float; no strings/Decimal |
| Interval | Tuple de dos Seconds en wire array: 0 <= t0 < t1 |
| PositiveInt | int no bool >0 |
| Nullable | Clave obligatoria con valor null cuando no aplica; ausencia nunca rellena una clave nueva |

Nuevos DTOs: Pydantic `extra=forbid`, `frozen=True`, validación estricta, `allow_inf_nan=False`. Arrays privados quedan en tuples. JSON dinámico validado queda como texto canónico inmutable; sus accessors devuelven copia nueva. No almacenar dict/list mutables accesibles en un objeto frozen.

`FrozenJSON` acepta solamente null/bool/int/float finitos/str/dict con claves str/list, antes de congelar. Rechaza ciclos, objetos Python, sets, bytes, claves duplicadas en JSON wire y tipos coercibles. Un mapping caller se copia antes de capturar.

JSON canónico nuevo: `json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",",":"), allow_nan=False).encode("utf-8")`. Sin BOM, newline final ni normalización Unicode/NFC. Arrays mantienen orden. No aplicar JCS ni modificar los codecs M1.

Seconds se normaliza a float durante captura y se emite como float. El reader de receta nueva valida la representación canónica de captura; no corrige un envelope con otra representación. Así `1` en lugar del Seconds ya capturado `1.0` no altera silenciosamente el SHA. Floats en params/descriptores conservarán su tipo original. `-0.0` se conserva en JSON dinámico; un intervalo permite cero firmado y no lo reescribe tras el sello.

### 4.3 CreativeRecipeV1: claves obligatorias

| Campo | Tipo y significado |
|---|---|
| `owner_id` | ULID del propietario local |
| `song_id` | ULID de la raíz de contenido |
| `job_id` | ULID del nuevo job que produce el take |
| `take_id` | ULID del nuevo destino; una receta por take, n_outputs=1 |
| `root_id` | ULID de raíz canónica de los padres |
| `derivation` | Literal `variant/extend/repaint/cover/edit`, coherente con operation |
| `operation` | Unión cerrada de ocho variantes, discriminada por `kind` |
| `executor` | Unión `InferenceSelection` / `CpuSelection`, discriminada por `kind` |
| `parents` | Tuple de 1 o 2 `ParentSnapshot`; todos los padres reales, orden semántico |
| `lyrics` | `LyricsContext`, letra histórica efectiva y bindings de padres |
| `required_features` | Tuple de nombres únicos ordenados lexicográficamente; nombres exactos del descriptor seleccionado |
| `sampling` | `{"index_rule":"round_half_up","interval":"half_open"}` |
| `commercial_use` | bool; conjunción de derechos de todas las entradas, selección y herramientas |

Esta versión no admite original sin padre, más de dos padres directos, preview sin take, texto ni providers. Son contratos de otras unidades. Una ampliación incompatible exige otro kind/schema_version, no extras permisivos. T02 no selecciona sus handlers.

La receta musical tiene `executor.kind=inference`; su nuevo modelo/semilla son selección para el futuro envío, no afirmación de inferencia completada. CPU tiene `executor.kind=cpu_edit`, `job.task` posterior `audio.edit` y `derivation=edit`. CPU no tiene campos model/seed/engine/winning_attempt/terminal/execution_id. La ejecución CPU durable nace después y no es parte de captura.

### 4.4 Padres, assets, derechos y antecedentes

`ParentSnapshot` tiene exactamente:

```text
ref: {type: Literal["take"], id: ULID}
owner_id: ULID
song_id: ULID
job_id: ULID
root_id: ULID
role: Literal["source","crossfade_a","crossfade_b"]
status: Literal["ready"]
asset: MasterAssetSnapshot
origin: ParentInference | ParentCpuEdit
lyrics_version_ids: tuple[ULID,...]
section_map: SectionMapIntent
commercial_use: bool
```

`MasterAssetSnapshot` tiene exactamente `ref:{type:"asset",id:ULID}`, `owner_id`, `subject_type:"take"`, `subject_id:ULID`, `role:"master"`, `sha256:SHA256`, `bytes:PositiveInt`, `media_type:Literal["audio/flac","audio/wav"]`, `duration_s:Seconds>0`, `sample_rate:PositiveInt`, `channels:Literal[1,2]`, `manifest_ref:{type:"asset",id:ULID}`, `manifest_sha256:SHA256`, `rights:ParentRights`.

El asset y su manifiesto acreditan pertenencia por subject. No añadir un `asset.song_id` inexistente. El recipe no copia paths ni metadata libre del asset. Los bytes y metadatos deben venir de inputs ya resueltos por el server; el DTO sólo valida coherencia interna.

`ParentRights` tiene `kind:"generated_take"`, `manifest_sha256:SHA256`, `commercial_use:bool`, `inputs:tuple[InputRights,...]`. M2 usa takes generados; uploads directos permanecen fuera del alcance. `InputRights` conserva declaraciones heredadas si existen: `ref:{type:"upload",id:ULID}`, `sha256`, `rights:Literal["own","licensed","consented","public_domain"]`, `consent:Literal["self","consented","n_a"]`, `real_person:bool`, `commercial_use:bool`. Un real_person exige self/consented. No inventar `rights:own` sobre un take generado. Si un manifiesto histórico no puede acreditar una declaración necesaria, la nueva captura falla; el reader legacy conserva la ausencia.

`ParentInference` tiene `kind:"inference"`, `model_id`, `model_version` (strings no vacías <=512), `seed:HistoricalSeed`. Son los campos reales de Take, capturados como antecedentes. No insertarlos en `CpuSelection`.

`ParentCpuEdit` tiene `kind:"cpu_edit"`, `recipe_sha256:SHA256`, `execution_id:ULID`. Sólo permite capturar un padre CPU cuando su autoridad durable real existe. No exige model/version/seed nulos dentro de esta variante: esas claves están prohibidas. La fila Take futura debe cumplir ADR-0074 al integrar.

Relaciones verificadas puramente: parent owner/song igualan raíz de recipe; parent.job_id no es nuevo job_id; asset.subject_id iguala parent.ref.id; asset.owner_id iguala propietario; refs de master/manifest distintas; rights.manifest_sha256 iguala manifest_sha256. Parent no es destino y parent.asset IDs no son compartidos por padres distintos. No padres duplicados ni autoaristas. No exigir globalmente que owner/song/job IDs de tipos diferentes sean distintos: los fixtures M1 reutilizan ULIDs.

Todos los parent.root_id provienen del linaje real verificado por el caller; recipe.root_id=min(parent.root_id). Captura pura no puede demostrar DAG ni resolver originales transitivos. T06 verificará el DAG; no inventará root_id buscando el menor padre directo.

### 4.5 Letra efectiva y autoría

`LyricsVersionSnapshot` tiene exactamente `id:ULID`, `owner_id:ULID`, `song_id:ULID`, `parent_id:ULID|null`, `text:str`, `sha256:SHA256`, `source:Literal["manual","assistant","import"]`, `declaration:Literal["own","assistant","public_domain","licensed"]`. El SHA es del texto exacto UTF-8. Preserva CRLF, etiquetas y direcciones editoriales. Rechaza surrogate Unicode, NUL y controles distintos de TAB/CR/LF. No elimina etiquetas ni interpreta texto como código.

`LyricsContext` tiene exactamente `mode:Literal["single","instrumental","composite"]`, `versions:tuple[LyricsVersionSnapshot,...]`, `target_version_id:ULID|null`, `parent_bindings:tuple[LyricsParentBinding,...]`, `commercial_use:bool`. `LyricsParentBinding` tiene `parent_id:ULID` y `version_ids:tuple[ULID,...]`. Versions se ordena por id; bindings conserva orden de parents; version_ids se ordena y no repite.

Todas las versiones son propias de recipe.song_id, sus hashes concuerdan y cada ref usada existe en versions. Sin versiones sobrantes: versions es exactamente la unión de bindings más target_version_id. Rechaza parent_id de letra igual a su id; pertenencia real y existencia del padre textual se revalidan en integración.

Los bindings igualan exactamente cada `ParentSnapshot.lyrics_version_ids`. Esos IDs proceden de `Take.lyrics_version_id` o del contexto creativo durable de un padre compuesto, no de `Song.current_lyrics_version_id`.

En `mode=single`, target_version_id es obligatorio no-null y aparece en versions. Para music.song, `executor.params.lyrics` es obligatorio y equivale exactamente a ese text. Si cualquier otra selección inference transporta params.lyrics, exige igualmente single y esa igualdad. Mantiene la declaración, sin exigir volver a declarar una autoría ya válida. Para music.instrumental, mode=instrumental, target_version_id=null, params no contiene lyrics y los bindings pueden conservar letras históricas del padre elegido. La letra previa no se borra por pedir instrumental.

Las tareas sobre audio pueden heredar autoría/letra del padre sin enviar letra al engine, si su descriptor no la exige. Si params no transporta lyrics, el contexto del target debe coincidir con el histórico del padre; no atribuye una letra editada nunca enviada. Una sustitución de letra en extend/repaint/cover exige su parámetro explícito declarado por descriptor y la versión correspondiente. Retake conserva su contexto histórico; no fuerza un parámetro lyrics que su descriptor no declare. El contexto de letra del hijo es metadata histórica y de autoría; únicamente la presencia exacta en params acredita texto enviado al engine.

CPU no genera ni reescribe texto. Si todos los padres tienen la misma única versión, single conserva esa versión. Si todos carecen de letra, instrumental tiene target null. En cualquier mezcla de versiones distintas, vocal/instrumental o padres compuestos, composite conserva todos los bindings y target null. El Take CPU no atribuye una única versión engañosa; la receta conserva las historias. No rechazar autorías distintas válidas ni transformar assistant en own.

Para variación_request, conservar exactamente la letra de la petición efectiva elegida, incluida su forma instrumental. Extend/repaint/cover pueden seleccionar otra LyricsVersion propia ya declarada; el DTO no crea una versión desde texto suelto. El target_version_id puede diferir de las versiones de padres únicamente en esas operaciones. Retake conserva el modo y versión histórica salvo que su descriptor verificado declare un parámetro de letra explícito; en esta versión no se habilita esa sustitución.

Las etiquetas y direcciones de `parse_lyrics` son contenido privado de la letra. No se convierten en operación, región o shell. Captura de letra no certifica alineación musical ni obediencia del engine. La validación editorial vigente conserva su responsabilidad posterior; T02 verifica identidad/hash/autoría, sin reescribir texto histórico.

### 4.6 Selección inference y CPU, parámetros y pins

`InferenceSelection` tiene exactamente:

```text
kind: Literal["inference"]
task: Literal["music.song","music.instrumental","music.retake","music.extend","music.repaint","music.cover"]
model_id: str no vacía <=512
model_version: str no vacía <=512
engine_id: str no vacía <=512
engine_version: str no vacía <=512
contract_version: Literal["1"]
mode: str no vacía <=512 | null
expected_image_digest: ImageDigest | null
descriptor: FrozenDescriptor
descriptor_sha256: SHA256
evidence_kind: Literal["learned","synthetic"]
synthetic_binding: SyntheticBinding | null
params: FrozenJSONObject
coordinate_params: CoordinateParams
seed: Seed
timeout_s: PositiveInt
output_shape: Literal["full","region"]
tools: tuple[ToolSelection,...]
```

`FrozenDescriptor` es un capturador NUEVO y aislado de M2, dentro de `creative/recipes.py`. Usa el ModelDescriptor público para validar tipos. No usa ni redefine CapturedDescriptor, SyntheticCapturedDescriptor, sus helpers privados, `_json_guard` o sus codecs M1. Los capturadores y bytes/hashes históricos de M1 permanecen intactos.

El wrapper es profundamente inmutable. Conserva `payload:bytes` canónicos y `sha256:SHA256`. Su `wire` devuelve una copia JSON nueva; su `value` devuelve un ModelDescriptor nuevo y separado. Su serializer dentro de la receta emite el objeto JSON de payload, no los campos del wrapper ni un string JSON doblemente codificado. Las firmas privadas nuevas son:

```text
FrozenDescriptor.capture(value: Mapping[str, object] | ModelDescriptor, *, evidence_kind: Literal["learned","synthetic"]) -> FrozenDescriptor
FrozenDescriptor.read(payload: bytes, *, expected_sha256: str, evidence_kind: Literal["learned","synthetic"]) -> FrozenDescriptor
FrozenDescriptor.payload: bytes
FrozenDescriptor.sha256: str
FrozenDescriptor.wire: dict[str, object] (copia nueva)
FrozenDescriptor.value: ModelDescriptor (copia nueva)
```

En captura nueva, copiar el JSON recibido y aplicar los límites/guardas M2 por namespace de §4.1/§4.9. Validar extras recursivamente contra los campos públicos de ModelDescriptor y sus modelos anidados ANTES de usar un parser público que los ignore. Los maps declarados de tasks/schema/features/limits conservan sus nombres permitidos; no aplicarles el veto substring token de M1. Un ModelDescriptor de entrada ya tipado se convierte a datos JSON separados, sin aliases. Validar estrictamente con ModelDescriptor y materializar explícitamente sus defaults existentes mediante model_dump(mode=json), una única vez en esta captura NUEVA. Aplicar de nuevo límites, cierres y guardas M2 al resultado antes de sellarlo con el codec canónico M2 de §4.2.

La lectura de un descriptor M2 sellado exige UTF-8/canonicalización exacta y SHA esperado sobre sus bytes originales. Validar estructura/tipos con el modelo público sobre una copia, sin volcar sus defaults al payload leído. Conservar ese payload/hash como autoridad. Si el modelo público añade un default posteriormente, su vista separada no redefine el JSON ni el hash del reader v1. No se usa ese reader para convertir descriptor/recibo M1; su lector histórico sigue vigente. InferenceSelection.descriptor_sha256 debe igualar FrozenDescriptor.sha256 y el SHA del objeto JSON realmente serializado dentro de la receta.

capture_recipe usa FrozenDescriptor.capture para una selección nueva. read_recipe/read_request extraen los bytes canónicos del nodo descriptor recibido y llaman FrozenDescriptor.read con selection.descriptor_sha256 y evidence_kind. No redirigen la lectura a capture ni a un validador que materialice defaults sobre el payload sellado. El DTO construido para lectura serializa exactamente FrozenDescriptor.wire, no FrozenDescriptor.value.model_dump().

La variante learned exige 1..64 weights; synthetic exige weights y remote_code vacíos. Ambas exigen 1..64 modes, provider local e identidades id/family/version/revision/license/training_data no vacías y de hasta512 caracteres. Weights/remote_code conservan paths relativos y formatos seguros del modelo público, con confinamiento lexical adicional M2: sin absoluto, URI, drive, backslash, segmentos vacíos/dot/dotdot ni controles. Captura no verifica archivos ni permisos. SyntheticBinding existente se admite como valor tipado validado y coherente con este SHA y su implementación, sin fabricar lease ni autorización runtime. Sus validadores existentes no se cambian.

Descriptor.id/version igualan selección. Provider debe ser local. Task debe existir y verified=true. Si mode es str, coincide exactamente con un modo del descriptor; si es null, no realiza esa comprobación de pertenencia y significa sólo modo no especificado en la selección /v1. Requiere igualmente descriptor.modes no vacío; no elige el primero ni rellena bf16. Null debe estar explícitamente presente, y variation_request conserva el null exacto del basis histórico. La proyección entrega null fielmente. El dato no certifica el modo realmente ejecutado: admisión/procedencia posterior lo observará; el producto debe exigir un modo explícito cuando la política de hardware lo requiera, antes de ejecutar y sin reescribir el basis/recipe sellado. Un recipe con null no habilita por sí solo esa ejecución.

Required features existen y verified=true. Evidence learned prohíbe synthetic_binding; synthetic exige binding coherente con descriptor SHA/engine/version/contract/image, y no acredita lease/registro runtime. Un flag synthetic aportado por el browser jamás concede autorización. La integración posterior debe rebind con SyntheticRegistry y comprobar la selección real.

`params` queda cerrado por el params_schema exacto de esa tarea. Validar el schema y usar `closed_schema` existente para vetar refs externas; esa función NO cierra los objetos. El contrato NUEVO exige additionalProperties=false en cada schema object de params, o rechaza la selección como RECIPE_INVALID. Registry sin red y referencias internas resueltas. No insertar defaults ni inventar nombres/escala de fidelity. Para lyrics/style se aplican sus límites específicos además de los del schema. Params no acepta campos secretos ni transporte/rutas de navegador aunque un schema mal configurado los permitiera. Cualquier param que nombre una feature verificada=false falla aunque no esté en required_features.

`CoordinateParams` tiene exactamente `at_s:str|null`, `t0:str|null`, `t1:str|null`. Valores no-null son nombres de propiedades NUMÉRICAS de nivel superior declaradas en params_schema.properties, de 1..128 caracteres; no JSONPath ni expresión. Extend requiere sólo at_s; repaint requiere sólo t0/t1 distintos; las demás operaciones requieren tres null. Params[name] coincide numéricamente con el campo de operation, con la tolerancia ideal definida en §4.7. El caller captura el binding aprobado por su adapter/descriptor; la receta no inventa los nombres reales de ACE-Step. La proyección no rellena ni modifica params. Así un punto/intervalo elegido no diverge de parámetros enviados. Sintéticos prueban mappings explícitamente declarados; una task real no verificada continúa rechazada.

`tools` es no vacío, tanto para CPU como para inferencia que requiere construcción/post CPU. Los pins son selección, no certificación de instalación. Inference.output_shape debe ser full en variation_request/variation_audio/cover; extend/repaint permiten full/region explícitamente, sin inferirlo de un nombre de adapter.

`CpuSelection` tiene exactamente `kind:"cpu_edit"`, `task:"audio.edit"`, `tools:tuple[ToolSelection,...]`, `output_format:{sample_rate:PositiveInt,channels:Literal[1,2]}`. No params libres. Trim/fade conservan sample_rate/channels del padre. Crossfade usa explícitamente formato del padre A; B puede requerir conversión posterior declarada por T03. Esta política no acredita fidelity, clipping ni ejecución de soxr.

`ToolSelection` tiene exactamente `tool_id:str` (patrón `[A-Za-z0-9._-]{1,128}`), `lock_sha256:SHA256`, `revision:str no vacía <=512`, `archive_sha256:SHA256`, `recipe_revision:str no vacía <=512`, `license:str no vacía <=512`, `commercial_use:bool`, `runtime_verified:bool`. Se ordenan por tool_id, sin duplicados. El lock SHA es SHA canónico del lock completo, compatible con `worker.packages.tool()`; no es el SHA del archivo ni del binario. El archive_sha procede del pin; no copiar su URL/dest/notas. La revisión FFmpeg y recipe_revision proceden de candidate.ffmpeg_commit/recipe_commit.

`runtime_verified=false` se conserva y no impide captura pura. Antes de admisión/render, el caller exige pin/runtime/licencia real verificados. El lock actual `ffmpeg-linux.lock.json` declara runtime_verified=false: esta propuesta no lo cambia ni lo presenta como verificado. Un fixture sintético puede modelar un pin verificado sin acreditar el tool real. La lista de herramientas no vacía no concede por sí sola commercial_use=true.

### 4.7 Operaciones cerradas y mapas de intención

Cada variante tiene sólo los campos de su fila. Kind determina task/origin/derivation y cardinalidad de padres. No expressions, graph nodes ni handlers aportados por cliente.

| operation.kind | Otros campos exactos | Executor / derivation / padres |
|---|---|---|
| `variation_request` | `basis:EffectiveRequestBasis` | inference song/instrumental; variant; source único |
| `variation_audio` | ninguno | inference music.retake; variant; source único |
| `extend` | `at_s:Seconds>=0` | inference music.extend; extend; source único |
| `repaint` | `region:Interval` | inference music.repaint; repaint; source único |
| `cover` | ninguno | inference music.cover; cover; source único |
| `trim` | `region:Interval` | cpu_edit; edit; source único |
| `fade` | `fade_in_s:Seconds>0|null`, `fade_out_s:Seconds>0|null` | cpu_edit; edit; source único |
| `crossfade` | `duration_s:Seconds>0` | cpu_edit; edit; padres A/B en ese orden |

At_s pertenece [0,duración padre], incluido final; region termina <= duración; crossfade duration<=min(duración A,B). Cada fade no-null<=duración y la suma<=duración; al menos uno no-null. Rechaza int bool/no finitos, intervalos vacíos/invertidos y solicitudes que dejan salida vacía.

`EffectiveRequestBasis` tiene exactamente `generation_job_id:ULID`, `winning_attempt_id:ULID`, `take_id:ULID`, `output_index:int>=0<=63`, `request_sha256:SHA256`, `request:FrozenJSONObject`, `lyrics_version_id:ULID|null`. El request es el JobRequest M1 real validado con cierre previo y tipos, conservando claves presentes; su SHA es el canónico vigente de sus datos, no bytes de un recibo. No insertar un pseudo-request desde Take.params o Song actual.

Basis.request tiene exactamente los diez campos de captured_request M1 enumerados en private_context.py: job_id/task/model_id/mode/inputs/params/seed/n_outputs/output_dir/timeout_s. No rellenar uno ausente por Pydantic; un basis incompleto no acredita petición efectiva. Request.job_id iguala winning_attempt_id; output_dir iguala tmp/<winning_attempt_id>. Los tipos cumplen JobRequest y seed efectivo no-null; output_index<n_outputs, seed+output_index<=2**64-1. Basis take iguala padre; generation_job_id iguala parent.job_id; task sólo music.song/instrumental. Basis.lyrics_version_id iguala lyrics.target_version_id; parámetros/letra instrumentales o vocales concuerdan.

Output_index selecciona la variante real. Semilla elegida anterior es request.seed+output_index; debe igualar parent.origin.seed y la nueva selection.seed debe ser distinta. Parent.origin.kind tiene que ser inference: esta operación no inventa una generación para un padre CPU. Los demás campos params/model/mode/timeout/task se conservan exactamente entre basis y selection; model_version concuerda con parent.origin.model_version y descriptor fijado. n_outputs del envío creativo nuevo es 1: no se replica un batch elegido ni su output_dir/job_id viejos. La comparación omite únicamente los identificadores técnicos del intento y n_outputs; no omite params arbitrarios. Basis.request.inputs debe estar vacío en esta versión: generación M1 desde uploads está fuera M2. Si no puede recuperar el intento/letra históricos, falla con RECIPE_CONTEXT_MISMATCH, nunca usa la canción actual.

`SectionMapIntent` tiene exactamente `kind:"requested_seconds"`, `ops:tuple[MapIntentOp,...]` (1..3). `MapIntentOp` tiene exactamente `op:Literal["keep","regen","append","fade"]`, `src:Interval|null`, `dst:Interval|null`.

Es un mapa de intención ligado al padre, no un `lineage_edge.section_map` efectivo. Nunca afirma índices finales ni duración medida. `dst=null` declara destino aún no resuelto por construcción; no se sustituye por duración deseada. `src=null` es obligatorio para regen/append, e inválido para keep/fade. Keep/fade tienen src dentro del master y, cuando dst existe, misma longitud ideal. dst de keep/fade sólo puede ser null tras una región de duración todavía desconocida en extend/repaint.

| Operación | Intento exacto por padre |
|---|---|
| variation_request, variation_audio, cover | Un regen con src=null, dst=null; declara sustitución completa |
| extend | Keep [0,at_s]→[0,at_s] si at_s>0; append null→null. Sufijo padre después del punto no se conserva. |
| repaint | Keep prefijo si region.t0>0; regen null→null; keep sufijo [t1,duración]→null si t1<duración |
| trim | Keep region→[0,longitud region] |
| fade | Una a tres piezas que particionan el padre: fade de entrada, keep central no vacío, fade de salida. Omite piezas de longitud cero. Dst de cada pieza iguala src. |
| crossfade A | Keep [0,A-D]→[0,A-D] si A>D; fade [A-D,A]→[A-D,A] |
| crossfade B | Fade [0,D]→[A-D,A]; keep [D,B]→[A,A+B-D] si B>D |

El DTO valida que el mapa proporcionado equivale exactamente a la operación y las duraciones capturadas. No acepta mapa arbitrario aunque sea numéricamente válido. Usa tolerancia absoluta 1e-9 segundos únicamente para comparar sumas de floats de estas identidades ideales; no es tolerancia de audio ni fidelidad. Orden ops cronológico. Crossfade solapa exclusivamente ambos fade en la duración D; sus roles no se intercambian. La operación fija envolvente lineal complementaria como política v1; T03/T08 resolverán índices y medirán clipping antes de declarar un mapa final.

La receta CPU conserva intenciones y antecedentes, nunca sustituye sus mapas por resultados después del sello. T03 resuelve índices de muestra una sola vez en el plan de construcción. La autoridad y el recibo de ejecución posteriores conservan el mapa efectivo, la duración medida y el vínculo a recipe_sha256. En su fase apropiada, el paquete/manifiesto y cada arista de linaje publicada reflejan esos resultados medidos. El renderer declara cambios de sample_rate/canales y su efecto sobre keep. No cambia bytes/hash de la receta ni del manifiesto ya emitido, conforme a Constitución §2. Esta separación no define el schema de CpuEditPlan/recibo ni integra publicación en T02.

`commercial_use` de receta equivale exactamente a AND de todos los parent.commercial_use, rights.commercial_use e inputs[].commercial_use, lyrics.commercial_use, tools[].commercial_use y descriptor.commercial_use cuando hay inference. Los flags parent/rights deben concordar. Instrumental sin versiones tiene lyrics.commercial_use=true como neutro. Para letra licenciada, el caller debe acreditar el permiso capturado: declaration=licensed por sí sola no permite asumir commercial_use=true. T02 valida los flags; no prueba derechos legales ni instalación.

### 4.8 Firmas privadas que T02 implementará

```text
capture_recipe(value: Mapping[str, object]) -> CapturedRecipe
capture_request(value: Mapping[str, object] | CapturedRecipe) -> CapturedRequest
read_recipe(payload: bytes, *, schema_version: int, expected_sha256: str) -> CapturedRecipe
read_request(payload: bytes | Mapping[str, object], *, expected_sha256: str | None = None) -> CapturedRequest | LegacyRequestView
canonical_bytes(value: CreativeRecipeV1 | CreativeRequestV1 | CapturedRecipe | CapturedRequest) -> bytes
canonical_sha256(value: mismos tipos) -> str
project_input_requirements(recipe: CapturedRecipe) -> tuple[RecipeInputRequirement,...]
project_engine_request(recipe: CapturedRecipe, *, attempt_id: str, inputs: tuple[ResolvedRecipeInput,...]) -> JobRequest
```

`CapturedRecipe` expone `value:CreativeRecipeV1`, `payload:bytes`, `sha256:str`. `CapturedRequest` expone `value:CreativeRequestV1`, `payload:bytes`, `sha256:str`, `recipe:CapturedRecipe`. Frozen wrappers y DTOs; `payload` siempre es bytes inmutable. Value.model_dump() y los accessors de FrozenJSON devuelven copias; mutarlas no cambia el wrapper. No accesores con diccionario backing compartido.

Capture valida sin efectos. Canonical functions sólo reciben DTOs/wrappers ya válidos: no normalizan una petición inválida ni aceptan JSON libre. Repetir captura del mismo contexto da mismos bytes/hash. Un recipe read exige hash externo y bytes canónicos exactos; request read verifica el recipe_sha embebido y la representación canónica antes de devolverlo. Expected_sha de request bytes siempre es SHA de payload crudo; de mapping es SHA canónico del mapping exacto recibido. Nunca mezclar ambos contratos.

La lectura bare recipe requiere schema_version=1 externo explícito; no intenta inferir versión por campos. La lectura envelope obtiene esa versión del campo obligatorio. Las dos proyecciones son puras: T02 las define y prueba; no llama al resolver, registra intentos ni abre archivos.

`RecipeInputRequirement` tiene exactamente `parent_id:ULID`, `asset_id:ULID`, `asset_role:"master"`, `engine_role:"source"`, `sha256:SHA256`, `media_type:Literal["audio/flac","audio/wav"]`. Variation_request devuelve tuple vacío. Retake/extend/repaint/cover devuelven un requisito desde su padre. CPU rechaza ambas proyecciones con RECIPE_CONTEXT_MISMATCH; nunca fabrica JobRequest engine. Los roles de crossfade son de linaje CPU, no roles de engine.

Antes de sellar una selección inference, validar sus requisitos previstos contra `descriptor.tasks[selection.task].inputs`. Repetir la misma comprobación pura en project_input_requirements y project_engine_request sobre los inputs efectivamente aportados. No usar la rama routing del resolver para omitir required. Construir el índice por role; si hay roles repetidos en el descriptor o los inputs, RECIPE_INVALID. Ningún input puede tener role desconocido. Todo spec.required=true debe estar presente. Cada input presente debe declarar un media_type incluido EXACTAMENTE en roles[input.role].media_types. Required ausente, role desconocido o media_type incompatible producen CAPABILITY_UNAVAILABLE, con field sanitizado y sin payload.

Variation_request aporta cero inputs y sólo es válida cuando la tarea elegida no tiene ningún input required. Un spec opcional no necesita aparecer. Para retake/extend/repaint/cover, la tarea debe admitir source con el media_type crudo del master capturado; ningún otro rol required puede quedar pendiente. Los roles de asset/master y lineage/source se mantienen separados de la comprobación de inputs del engine.

Ejemplo rechazado: parent.asset.media_type=audio/flac y task.inputs source sólo admite audio/wav. Aunque JobRequest acepte estructuralmente FLAC, la selección y proyección T02 fallan por incompatibilidad. No transcodificar, retaggear media_type ni reemplazar el SHA para hacerla pasar. Una futura conversión requerirá plan, herramientas y evidencia de bytes propios fuera T02; no existe una conversión implícita en este contrato.

`ResolvedRecipeInput` tiene exactamente `asset_id:ULID`, `role:"source"`, `path:str`, `sha256:SHA256`, `media_type:Literal["audio/flac","audio/wav"]`. Path aparece sólo en argumento privado de proyección entregado por server después de resolver/stage, jamás en recipe. Valida sintaxis relativa con Input del contrato engine y rechaza segmentos vacíos/dot/dotdot, absolutos, URI, backslash, drive y controles. Cada input debe igualar su requisito en asset/SHA/media/role, en orden y sin extras, y cumplir el descriptor task.inputs anterior. No lee ni verifica bytes ni acredita custodia; T06 lo hará sobre la entrada real.

La proyección crea una instancia JobRequest NUEVA con exactamente job_id=attempt_id, task/model_id/mode/params/seed/timeout_s de selection, n_outputs=1, output_dir="tmp/"+attempt_id e inputs desde los argumentos validados. Nunca usa recipe.job_id como ID del intento ni copia basis.output_dir. El engine recibe su /v1 actual y ninguna recipe/owner/song/private rights/binding. Mutar el JobRequest proyectado no altera recipe. No hace load ni pasa synthetic_binding al engine.

La integración no puede traducir `{ref:asset,role:source}` directamente a referencias M1: references.py exige asset.role==item.role y el master tiene role=master. RecipeInputRequirement conserva ambas nociones. T06 resolverá/verificará master mediante identidad estable y sólo después asignará engine_role=source a la entrada staged. Debe adaptar ese seam explícitamente y probarlo; no retaggear asset ni cambiar M1 en T02. No se agrega una forma de input no soportada al reader legacy.

Las comprobaciones de descriptor/input demuestran coherencia del snapshot capturado. No prueban que el backend vivo mantenga esa capacidad, que el archivo coincida con su SHA, que una task sintética autorice el motor real ni que exista custodia. Admisión/procedencia conservan su revalidación y gates runtime; T02 no los ejecuta.

`LegacyRequestView` expone `format:"m1_unversioned"`, `raw_payload:bytes|null`, `raw_sha256:str|null`, `canonical_payload:bytes`, `canonical_sha256:str`, `present_fields:tuple[str,...]`, y `value` como copia separada. No es una nueva receta ni un DTO M1 inventado. Mapping no conserva serialización cruda: raw_payload/raw_sha256=null explícitos. No afirmar que reconstructed bytes son el recibo original.

Error de captura/reader: `RecipeError(ValueError)` con `code` y `field:str|null` sanitizados. No incluye input, params, letra, path, secretos ni repr de Pydantic en mensaje/log. Field sólo permite ruta estructural conocida e índices decimales; claves dinámicas inválidas no se copian al error.

| Code privado | Casos |
|---|---|
| RECIPE_VERSION_UNSUPPORTED | kind/schema_version desconocidos o versión mal tipada |
| RECIPE_INVALID | forma, extras, rango, tipo, tamaño, duplicados, mapas |
| RECIPE_HASH_MISMATCH | SHA externo/embebido/canónico/descriptor/lyrics inconsistente |
| RECIPE_CONTEXT_MISMATCH | dueño/song/parent/dest/basis/roles/origin incoherentes |
| RECIPE_SECRET_FORBIDDEN | clave de secreto o credencial/URI/path en campo de transporte |
| LYRICS_DECLARATION_REQUIRED | falta declaración vocal efectiva en captura nueva |
| RIGHTS_DECLARATION_REQUIRED | falta prueba de derechos necesaria de nueva fuente |
| CAPABILITY_UNAVAILABLE | task/feature no verificada en selección inference |

No agrega estos códigos a HTTP/API durante T02. La integración posterior mapeará la estructura privada al ProblemDTO vigente; no inventar endpoint de recetas.

### 4.9 Readers históricos y privacidad

Dispatch nuevo: presencia de `kind` o `schema_version` compromete al formato nuevo. Si kind/version no son exactamente los soportados, falla. No tratar una versión futura como legacy. Si faltan ambos, el reader devuelve LegacyRequestView y conserva JSON recibido sin defaults. Rechaza secretos/non-JSON/no finitos y campos de transporte desconocidos, pero no exige request completo ni params/inputs/seed por defecto.

Forma histórica de dominio admitida: objeto con subconjunto de claves `params`, `inputs`, `seed`, `n_outputs`, `timeout_s`, `mode`, `required_features`; params es objeto, inputs usa exactamente `{role,ref:{type,id},output_index?}` y tipos take/asset/upload/job. Sólo valida los campos que existen. IDs, índices, tipos y no secretos se comprueban si presentes; no suplir roles ni output_index omitido. Seed/mode explícitamente null se conservan como permiten las peticiones de dominio M1; no se convierten a cero/bf16. Un seed grande histórico no se reduce. Reader legacy usa límite16MiB del recibo privado existente y no impone el límite1MiB ni string8192 de receta nueva. Cualquier efecto/capacidad lo valida todavía el consumidor M1.

Formas observadas en fuentes:

| Fuente real | JSON histórico que se conserva |
|---|---|
| `domain_routes.py` y `queue/chains.py` | params con lyrics/style efectivos, seed, n_outputs; fields opcionales presentes sólo cuando el caller los pasó |
| `queue/chains.py:add_dependents` | post.audio: sólo inputs con ref job/source/output_index; beats: params={} e inputs ref take/master |
| `test_snapshot_synthetic_provenance.py:98`, `test_job_attempt_schema.py:486` | Fixture request={"seed":17}; la aserción de preservación del snapshot está en test_job_attempt_schema.py. No params/inputs insertados. |
| `worker/contracts.py:PostPlan` | version=1, handler=post.audio, autoridad ganadora y descriptor; conserva su reader actual |
| `private_context.py:_validate` | version=1, winning_request_sha256, captured_request, song_id, takes; conserva su reader actual |
| `snapshots.py:canonical_row` | Omite provenance/provenance_sha256 nulos y error_code nuevo nulo; no añadir origin inferido ni defaults de recipe |

T02 no hace dispatch de PostPlan, manifiesto, private_context ni song snapshot completos. Sus readers actuales siguen siendo autoridad. Sus bytes/hash se preservan como fixtures de entrada y no se reserializan. Para probar T02, extraer solamente job.request de un snapshot sintético derivado de estas formas; no inventar una CreativeRecipe legacy.

El reader raw verifica SHA de bytes antes de parsear y conserva esos bytes. Validación JSON UTF-8 rechaza BOM, bytes inválidos, trailing data, duplicados, NaN/Infinity y objetos no finitos. Para legacy, whitespace/orden/escapes distintos se conservan en raw_payload; canonical_payload se calcula aparte y nunca reemplaza archivo o hash previo. Reader de mapping no toca el mapping ni la columna.

Secrets: normalizar claves con NFKC/casefold y conservar sólo ASCII alfanumérico. Comparar por IGUALDAD, nunca substring, con este conjunto cerrado: secret, secrets, token, accesstoken, refreshtoken, apitoken, enginetoken, studioenginetoken, studiotoken, password, passwd, credential, credentials, ciphertext, authorization, proxyauthorization, header, headers, apikey, providerapikey, privatekey. Aplica a claves de datos dinámicos en params/basis.params y a claves inesperadas de DTO. Los DTO de campos fijos ya rechazan toda clave extra. `tokenizer`, `max_tokens`, `token_budget`, model_id cuyo VALOR contiene token y texto artístico con la palabra token no coinciden y no se bloquean por ese término.

Namespaces de descriptor/pin/schema no son diccionarios de credenciales: validación cerrada contra sus campos y esquema; allí no aplicar lista de claves a los nombres DECLARADOS bajo params_schema.properties/features. Una propiedad `token` del schema no es un token transportado. Si params trae ese nombre como valor de datos, la política anterior lo rechaza aunque el schema lo admitiera. Weight.path/RemoteCode.path se validan como paths de pesos, no como credenciales ni entrada musical. SyntheticBinding.origin conserva su URL local /v1 ya validada sin userinfo; no es parámetro de navegador.

Prohibir blobs inequívocos en cualquier string de datos, incluso lyrics/style. Las tres reglas son independientes:

- PEM: rechazar `-----BEGIN PRIVATE KEY-----` y sus variantes RSA/EC/OPENSSH.
- Bearer: rechazar `Bearer ` seguido de al menos16 caracteres ASCII alfanuméricos o de `._~-+/=`. La palabra aislada no activa esta regla.
- URI: rechazar userinfo de username/password identificado mediante urlsplit.

El texto que diga "mi token" sigue siendo lícito. La política tiene falsos positivos delimitados de blobs completos. No interpreta lenguaje ni detecta cualquier secreto sin formato. Campos cerrados y caller server-side autorizado completan la garantía. El error nunca conserva la clave ni el blob rechazados.

Nuevos params no transportan path/output_dir/url/headers/credentials/scripts/commands ni ref libre. El descriptor sí conserva paths relativos de weights/remote_code ya validados por ModelDescriptor; no tratarlos como rutas de entrada de navegador. Recetas jamás reciben paths de audio, output_dir ni lease/PID/estado de custodia. Lyrics puede contener texto artístico parecido a una ruta sin volverlo una referencia ejecutable.

DTOs, raw/canonical bytes y lectores son privados. No se copian a manifiestos públicos, eventos, respuestas genéricas, logs, Git ni fixtures reales. T04 usa datos sintéticos marcados. El SHA solo prueba integridad de la captura, no autorización, instalación, resultado ni custodia.

### 4.10 Casos que debe probar la implementación después de RED

| Grupo | Evidencia exigida en tests T02 futuros |
|---|---|
| Deep immutability | Mutar nested params, descriptor, derechos, maps, arrays y model_dump tras captura deja bytes/SHA iguales; asignación DTO falla |
| Determinismo | Orden de keys distinto produce mismo hash; orden de padres/ops distinto es rechazado o conserva diferencia semántica; UTF8/CRLF/acentos exactos |
| Versiones | Falta schema_version, bool/float/string/2, unknown kind/operation/executor; ninguno cae a legacy |
| Estructura | Extras en cada DTO/anidado, cycles, tuple Python en JSON dinámico, duplicate JSON keys, >1MiB/depth/colecciones, NaN/Infinity/bool Seconds |
| Secretos/privacy | Claves NFKC/ofuscadas, password/headers en params; URI userinfo/PEM/Bearer; texto editorial lícito; errores no contienen entrada |
| Relaciones | Owner/song ajenos, parent=dest, parents duplicados, manifest/master mismo id, asset sujeto ajeno, hash rights distinto, root incorrecta |
| Mapas/roles | Crossfade pierde/invierte padre/rol/map; fade doble fuera de duración; src/dst arbitrario; extend final sin keep vacío; repaint completo sin keeps vacíos |
| Letra | SHA/ID/text discordantes; autoría ausente; single inválido; composite completo; instrumental conserva letras históricas; no lectura de Song actual |
| Basis | Request del ganador completo; nuevo seed distinto de variante efectiva; params/timeout/model/mode cambiados rechazan; selección de otro output; basis sin evidencia falla |
| Selección | Params extra/no cerrados, refs de schema remotas, feature/task false, coordinate_params discordante, mode/model/descriptor hash incoherentes, sintético sin binding, CPU con engine/model/seed/attempt/execution |
| Descriptor M2 aislado | Schemas con properties token/tokenizer/max_tokens/token_budget válidos se capturan; params.token real se rechaza. Extras anidados, peso/remote path inseguro, provider externo, synthetic con weights o learned sin weights fallan. Defaults se materializan sólo en captura nueva; reader conserva bytes/SHA originales. Ningún test cambia M1. |
| Proyección pura | Attempt/output_dir nuevos; n_outputs=1; input source resuelto coincide con asset master/hash/media y task.inputs; falta/sobra/input path inválido; ningún dato privado en JobRequest; CPU rechaza; mutar resultado no modifica receta |
| Compatibilidad inputs | FLAC master/WAV-only descriptor rechaza antes de sello y proyección; source role desconocido, required extra ausente, roles duplicados del descriptor/input y media incompatible fallan. Variation_request cero inputs acepta sólo todos optional. Cambio media/SHA para fingir conversión falla. Modelo/capacidad viva y bytes/custodia siguen fuera de esta prueba. |
| Pins/derechos | Pin archive/hash mal formado, tool IDs duplicados, commercial_use=true con padre/tool/model false rechaza; runtime_verified=false se captura sin habilitar |
| Legacy | request seed-only, post inputs, beats; whitespace y escapes raw intactos/hash crudo; faltas no rellenadas; origen no agregado; mapping original intacto |
| Lectura sellada | Bytes alterados, recipe_sha externo/embebido distintos, representación no canónica nueva, doble versión, JSON duplicado; no normalizar para ocultar discrepancia |
| Límite de autoridad | Todos los tests son CPU puros sintéticos, sin SQL/GPU/LLM/Docker/archivos musicales; capture no publica/encola ni modifica M1 |

La Verificación T02 sigue siendo `uv run pytest -q apps/server/tests/test_creative_recipes.py`. Esta pasada no la ejecuta porque no implementa producto. TDD n/a: prosa de diseño. No registra un RED/GREEN ni aceptación de la tarea.

## 5. Impacto en módulos y ficheros

| Ruta real o destino nuevo declarado | Cambio propuesto | Alcance |
|---|---|---|
| `apps/server/app/creative/__init__.py` | Exportar DTOs/wrappers/readers privados | Nuevo T02 |
| `apps/server/app/creative/recipes.py` | Contrato descrito en §4, puro y sin efectos | Nuevo T02 |
| `apps/server/tests/test_creative_recipes.py` | RED/negativos/regresión inmutabilidad y legacy | Nuevo T02 |
| `docs/arquitectura/iteracion-creativa.md` | Explicar captura/lectores, límites y privacidad | Nuevo T02 |
| `apps/server/app/queue/chains.py`, `resolver.py`, `references.py`, `admission.py` | Futuro dispatch/proyección y transacción de refs válidas | Fuera T02; T06 |
| `apps/server/app/worker/contracts.py`, `planning.py`, `publications.py` | Autoridad/plan/recibo nuevo después de captura | Fuera T02; T07 |
| `apps/server/app/snapshots.py`, schemas song/manifest | Preservar v1, integrar v2 CPU en sus propias unidades | Lectura solamente aquí |
| `packages/contracts/creative-recipe-v1.schema.json` | Exportación code-first del DTO elegido | Nuevo T04, no escrito ahora |

La preparación original se escribió sólo en un namespace privado. ROOT incorpora este contrato y conserva el índice ADR, ledger y Git. La implementación posterior sólo posee sus archivos declarados; no ejecuta formatters globales ni reescribe documentos compartidos.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Envelope remitido al resolver legacy | Alta sin dispatch | Trabajo inválido o petición rechazada | Separar captura T02 de integración T06; testar proyección al integrar |
| Captura parece autoridad CPU | Media | Publicación sin recibo/custodia | No execution/terminal/attempt en recipe; T07 exige autoridad propia |
| Canonicalización cambia histórico | Alta si se usa DTO/defaults nuevo | Hash/snapshot roto | Reader legacy conserva raw y presence; no convierte a recipe |
| Parent CPU compuesto pierde letras | Media | Autoría falsa o historia perdida | Bindings completos y composite explícito; no forzar una sola LyricsVersion |
| Requested map parece mapa efectivo | Media | Procedencia falsa | Namespace section_map.kind=requested_seconds; T03 no modifica receta sellada |
| Task real no verificada entra por sintético | Media | Capacidad ficticia | Snapshot coherente sólo; integración exige registry real/gate |
| Tool actual no verificado aparece como instalado | Alta por lock false | Render no reproducible | Capturar false fielmente; gate previo a admisión/render |
| Nuevo tamaño/cierre rechaza un histórico grande | Media | Regresión de lectura | Reader legacy usa límite M1 16MiB, no límite nuevo 1MiB; no valida con DTO receta |
| Fuentes compartidas cambian durante diseño | Media | Propuesta desactualizada | Hashes antes/después; comunicar drift a ROOT sin revertir |

## 7. Preguntas abiertas

No quedan campos/tipos/firmas abiertos para T02. ROOT ratifica el detalle antes del RED tras revisión A+B intento 2 y QA documental 18/18. Los cambios incompatibles posteriores requieren decisión y versión propias; esta aceptación es documental.

Fuera T02: formato completo CpuEditPlan/recibo/paquete/CAS; integración transaccional; migración; export/import CPU; medidas de audio/custodia; previews A/B; LLM/providers. Estos contratos se fijarán antes del RED de sus propias unidades. No bloquean la captura pura aprobada.

Durante la preparación original, la última decisión observada era ADR-0076. ROOT comprobó nuevamente la numeración e incorpora ADR-0077 con este contrato; no había otro archivo con ese número.

### Evidencia documental de la preparación inicial

Recon de fuentes reales descritas en §1/§4.9; lectura del brief completo en dos tramos, Constitución, datos/convenciones, spec/design/plan/ledger y ADR-0073/0074. `knowledge-find.py --tipo adr --contexto 'M2 iteración creativa recetas privadas'` con entorno gestionado: exit 0, sin aciertos. No hubo prueba de producto, escritura de BD ni integración.

Verificación documental ejecutada: `rg -n '\{\{|<[!]--' design.md ADR-0077-envelope-privado-de-recetas-creativas.md` no produjo coincidencias (exit1 esperado). `rg '^## [1-7]\.' design.md` devolvió las siete secciones exactas (exit0). El último ADR observado en esa preparación era0076. Los hashes finales de los dos documentos se entregan a ROOT aparte, para evitar un hash autorreferente. No hubo pruebas de producto; TDD n/a: prosa. Un check intermedio encontró sólo la cadena del comando escrita en este párrafo; se corrigió su representación para que el check no se autoseñale.

Hash audit documental: 31 fuentes examinadas, 30 byte-idénticas al finalizar. Sólo tasks.md cambió por ROOT, que avisó su nueva SHA 126f4f300b6a637b72612631f9460c7c99649813e8136ebcc1da2deaa0fe7506. No se revierten cambios ajenos. El siguiente inventario registra pre/post; igual significa SHA final igual al inicial.

| Fuente relativa | SHA256 antes | Después |
|---|---|---|
| `docs/roadmap/2026-10-10-m2-iteracion-creativa/spec.md` | `1cb6a36d6b0be15d814aff1839c76649bce3b93c08b71e5af0ee7988e94f5180` | igual |
| `docs/roadmap/2026-10-10-m2-iteracion-creativa/design.md` | `9aaf027a675de2b8f14b181139d44aa422094d7731644619a1f1d1c861f2f419` | igual |
| `docs/roadmap/2026-10-10-m2-iteracion-creativa/cpu-contract-design.md` | `507ecc1e5b9f77ea7a253e9fcf38b6c681c0bb12a4cc8e1354ef2c3f486fcd9e` | igual |
| `docs/roadmap/2026-10-10-m2-iteracion-creativa/improvement-plan.md` | `f7e269dcba3a799053bff9a51771e8e31d58e76788f2b7c7db6b0c3f59e421e2` | igual |
| `docs/roadmap/2026-10-10-m2-iteracion-creativa/tasks.md` | `cc3070f98817f769a11285b0bbfe803933a3da6eddd1acbefcef03f6a0bb00d3` | `126f4f300b6a637b72612631f9460c7c99649813e8136ebcc1da2deaa0fe7506` |
| `docs/decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md` | `f5e4cc7197dd1cede3f77d81971e11444d3437198d333ce3bd50c93d599f5283` | igual |
| `docs/decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md` | `0174e9cc195c8c784b909abfe730ed60bcb593983dc525b74b25299a285b5ffd` | igual |
| `docs/CONSTITUTION.md` | `b15df6b30747dbe594d97a8fe2f896509586da4b890de981c42c1f27234861b2` | igual |
| `docs/arquitectura/datos.md` | `a5ffb07c5de4e8598162e91338868f14772ca0fdcd82ebb13c23dbcc4f2f3547` | igual |
| `docs/arquitectura/convenciones.md` | `77a0745f0e7c45b2c5b4c7af348435149f88c96a986f71d68e484d02d5cc491b` | igual |
| `apps/server/app/models/__init__.py` | `9c86ef171968e799908068c1f98ce47186b9e2ed3337c019a7e9696d38dac0df` | igual |
| `apps/server/app/domain_routes.py` | `ecec486608fac6a59e0cfef111f523c321fe5c841fb62ca5944b9938b03f7e12` | igual |
| `apps/server/app/queue/chains.py` | `65bbbf0a53a121e2c4efaaa95df73d8d1764eba09b51cb9debfdc667df5eeb7f` | igual |
| `apps/server/app/queue/resolver.py` | `8278f3c623ebd7bd7e55ad6d40dade4f86ee809d63407c0379fe5bd9db630b68` | igual |
| `apps/server/app/queue/admission.py` | `6e15b6a99924fa5cf4b1f406430cb3a4e4ce0b538384333b2345cbc89d0ca94b` | igual |
| `apps/server/app/queue/dispatcher.py` | `832284d9fc94dbaeddc9e5b3843fd91886d6891e4ad6f653f0feb317903ca7e7` | igual |
| `apps/server/app/queue/references.py` | `ae565b7182a8512a17b18a76578980be6b6407b062b2bea101ca4fbdb81a1017` | igual |
| `apps/server/app/queue/inputs.py` | `1b5460402cc59e5720b61fadc171216d40a23ae1ce3e1af5844d2cfbe8483890` | igual |
| `apps/server/app/queue/provenance.py` | `44300f1090b7b182eaf5d1a8ce65aaa078c17738c261e097977963e57a025ea4` | igual |
| `apps/server/app/worker/contracts.py` | `4c04a5a5698e88ab1d31f65e9f3924e6b63e077b6dc2ee282f35da2c85fb891b` | igual |
| `apps/server/app/worker/planning.py` | `3aca3783d91b398fc4932f0c61759563cc2a1d4088ce23ef81b0186148bb8dcd` | igual |
| `apps/server/app/worker/packages.py` | `638f944a1a6fba57ebf91952f9ff3c7f780619812abe5a38c1646a71d18e77ba` | igual |
| `apps/server/app/snapshots.py` | `61189b40618a86bdaf7cd0266ab565112b55dc2de053875925c4567fff8c46f4` | igual |
| `packages/audio-post/audio_post/private_context.py` | `0397c05c53785f9068daef896ef92fb3a3c9a2ed6772dfb7f790ac9ad6c65c23` | igual |
| `packages/engine-contract/engine_contract/__init__.py` | `bab72f90bc4ab530154eeb4756d3727dd851321f7dc60224a7f0a443e9934756` | igual |
| `apps/server/tests/test_worker_contracts.py` | `fc33331ff162f451a0993ca3f2efae267fa8f3949213dade03bae94caf2d93ec` | igual |
| `apps/server/tests/test_worker_snapshots.py` | `d1f9d005dd63bcbc7232927359c9e8e121d96bac5acce0a8238f84d91026dfe4` | igual |
| `apps/server/tests/test_snapshot_synthetic_provenance.py` | `2886ee180c2f200c0c0470edc29979f90b88b9a803a418024c328ca915a56a00` | igual |
| `tools/ffmpeg-linux.lock.json` | `59742314f662523a09489a79cf7fdbdedcf5f3dd22e75fe683ad9f4659b27c99` | igual |
| `.cache/dev-cycle/m2/creative-recipes-t02-20261011/task-brief.md` | `f283d1333a2643011999ee5bcfc3b1aeaba03126eb42712ab424927a19b87e6b` | igual |
| `.cache/dev-cycle/m2/creative-recipes-t02-20261011/actor/needs-context.md` | `7620a32cbe91eb5d53d447d3f8c28b3499be8744fadde59fd353982eff32d72b` | igual |

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-11 | Tres opciones reales; ROOT elige O1 bajo delegación. Propuesta íntegra privada para revisión antes del RED. |


### Ratificación ROOT — 2026-10-11T11:30:04.875828+00:00

Contrato O1 aprobado bajo delegación. Revisión A+B intento2 sin gaps; QA documental18/18/gate0. El informe de QA conserva intento1 16/18/gate1 por dos sondas literales corregidas sin cambiar documentos. ROOT verifica50entradas de artefactos,34fuentes canónicas y36snapshot. Esta ratificación no acredita código, TDD, admisión, ejecución ni aceptación T02/M1/M2.
