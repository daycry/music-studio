---
design: m2-t03-private-composition-contract
titulo: Planes de composición cerrados sobre hechos de buffers
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: spec.md
evaluacion: n/a
plan: improvement-plan.md
adr: ../../decisiones/ADR-0079-composicion-creativa-por-muestras-medidas.md
opcion_elegida: O1
validacion_opcion: ROOT bajo delegación vigente del propietario; selection-root.receipt.json, 2026-10-11T13:43:01.014657+00:00
revision_contrato: pendiente de revisión documental y QA por ROOT
destino_propuesto: docs/roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md
recomendada: O1
model_tier:
  agente: architect
  model: opus
  effort: high
  fuente: frontmatter del recibo ROOT; no afirmación de modelo ejecutado
generacion:
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  nota: Prosa sin estimación de consumo. ROOT conserva el único marcador abierto.
---

# Contrato de composición M2/T03 — O1 elegida, revisión pendiente

## 1. Contexto y restricciones

T02 está completada según el recibo de ROOT. Esta propuesta concreta `apps/server/app/creative/composition.py` y `apps/server/tests/test_creative_composition.py`, aún no implementados por este actor. Respeta O2 global y los contratos aceptados de ADR-0073/0074/0077. ROOT eligió O1 bajo delegación vigente el 2026-10-11. El contrato detallado sigue en borrador: ROOT publicará sólo tras revisión documental y QA. Esta preparación no aprueba el diseño ni el ADR. TDD n/a: prosa. No se ejecutó la verificación de producto ni se atribuye resultado a T03.

Fuentes vigentes: [receta §4.7](recipe-contract-design.md), [recetas implementadas](../../../apps/server/app/creative/recipes.py), [datos §1.2](../../arquitectura/datos.md), [ADR-0041](../../decisiones/ADR-0041-esquema-inicial-y-snapshots-del-server.md), [diseño CPU](cpu-contract-design.md), [test-plan: método y tolerancias](test-plan.md). Los enlaces relativos ya corresponden al destino propuesto composition-contract-design.md del roadmap. El ADR-0079 enlazado sigue siendo propuesta privada hasta incorporación por ROOT.

T03 es pura CPU: no I/O de audio/archivos, FFmpeg, GPU, SQL, jobs, takes, rutas, custodia, publicación ni inferencia. No crea recibos de ejecución. Los hashes de facts identifican datos aportados; T03 no demuestra que existan esos bytes. Una evidencia sintética sólo sirve al test identificado, nunca al backend real. No exporta un grafo editable.

T02 sella `requested_seconds`, `sampling={index_rule:round_half_up,interval:half_open}`, selección `output_shape` y hashes. T03 jamás modifica su `CapturedRecipe.value/payload/sha256`, descriptor o selection. El plan es otro artefacto ligado a ese SHA. Sus mapas resueltos todavía no son mapas efectivos probados por audio. La autoridad/recibo posterior vincula recipe SHA, plan SHA y mediciones propias; no reutiliza el hash del plan como prueba de ejecución.

## 2. Opciones (3)

### O1 — Cierre con hechos de todos los buffers, incluida conversión

Preflight puro declara conversiones necesarias sin resolver índices. El caller convierte y mide fuera de T03. La construcción final recibe facts originales y convertidos, resuelve coordenadas una vez y sella un plan cerrado. El renderer consume ese plan sin volver a redondear segundos.

### O2 — Plan paramétrico y cierre de índices dentro del renderer

T03 produce segundos, operaciones y formato objetivo; T08 convierte/mide y resuelve índices. Es una alternativa viable de responsabilidad, pero no satisface que T03 resuelva muestras una vez ni sus negativos de duración antes de render. Requiere cambiar el alcance fijado de T03; se descarta bajo el brief actual.

### O3 — Composición limitada a formatos iguales

Plan cerrado inmediato sobre masters/salida engine con rate y canales idénticos. Rechaza toda conversión. Reduce el seam inicial, pero crossfade B distinto está permitido por T02 y requiere una ampliación explícita antes de habilitar esos casos. Es una entrega reducida, no el contrato completo solicitado.

| Opción | Complejidad | Riesgo | Coste relativo | Reversibilidad |
|---|---|---|---|---|
| O1: facts de todos los buffers | Media | Bajo: no estima frames; seam de conversión explícito | M | Alta: formato privado independiente de M1 |
| O2: cierre dentro del renderer | Baja en T03, alta en T08 | Alto: autoridad temporal repartida y negativos tardíos | M | Media: consumidores dependerían del renderer |
| O3: formatos iguales | Baja | Medio: operaciones válidas en T02 quedan indisponibles | S | Alta: ampliación posterior versionada |

## 3. Criterios de decisión

1. Índices finales sobre frames medidos; ninguna duración deseada sustituye facts.
2. Receta/descriptor inmutables y compatibles con T02 y readers históricos.
3. Full consume sólo el buffer completo del engine; region ensambla exactamente una vez.
4. Cada padre conserva su arista/rol/raíz y su coordenada original, incluso con conversión.
5. Diferenciar construcción, procedencia y fidelidad todavía pendiente.
6. Contrato cerrado reutilizable por T08/T07/T11–T14, sin crear otro dominio de edición.

## 4. Opción elegida y por qué · contrato normativo candidato O1

O1 elegida por ROOT conforme a los criterios 1, 3 y 4: índices finales sobre hechos medidos, conversión explícita y una única construcción de cada shape. O2 desplaza a T08 una responsabilidad fijada de T03; O3 omite conversiones permitidas por T02. ROOT ratificó las políticas detalladas mediante selection-root.receipt.json. Elegir O1 no acredita revisión del contrato, implementación, ejecución ni aceptación de T03/M2. Véase [ADR-0079 propuesto](../../decisiones/ADR-0079-composicion-creativa-por-muestras-medidas.md), aún no incorporado al canon.

### 4.1 Autoridad del caller y facts

El caller autorizado revalida owner/song/ready/derechos, DAG/raíces originales y hash real de cada master; mide frames decodificados, sample rate y canales. Para inferencia aporta facts de un resultado capturado y su descriptor/shape sellados; la asociación con el terminal ganador es del caller posterior, nunca de un engine ficticio creado aquí. T03 comprueba coherencia de datos recibidos, no sustituye esas autoridades.

Todas las claves de DTO son obligatorias, incluidas las nullable. Pydantic cerrado, congelado, estricto, sin NaN/Infinity; arrays son tuples inmutables. No `model_construct` sin validación ni mappings/listas compartidos. Reutilizar tipos públicos privados T02 `ULID`, `SHA256`, `CapturedRecipe`, sin importar codecs/guards M1. Enteros exactos: `type(x) is int`, nunca bool; floats no coaccionados de str/Decimal. Sólo channels 1 o 2.

`BufferId` es el mismo Literal de cinco IDs de BufferFacts; `ParentRole` es Literal[source,crossfade_a,crossfade_b]. `ToolSelection` es el DTO existente T02, no una copia que cambia sus pins.

`AudioFormat = {sample_rate:int[1,2**31-1],channels:Literal[1,2]}`. `FrameSpan` en wire array de dos enteros exactos `0<=start<stop<=2**63-1`; no vacío. `frames:int[1,2**63-1]`. Toda suma/resta/frame index se comprueba dentro de ese rango antes de construir el DTO. No asigna arrays de tamaño frames.

`NominalFrameRange` en wire array de dos enteros exactos `0<=start<=stop<=2**63-1` permite igualdad. Sólo describe procedencia nominal de B convertido, mediante el campo `nominal_src`. Nunca ocupa `dst`, `render_span`, `RenderTerm.span`, `src` ni `conversion_scope`. Un rango nominal vacío no declara ausencia de dependencia; el scope completo conserva esa dependencia. La propuesta FIX1 añade esta representación; su ratificación corresponde a ROOT.

`MeasurementRef = {evidence_id:ULID,evidence_sha256:SHA256,evidence_kind:Literal[measured,synthetic]}`. Referencia opaca, sin ruta ni texto libre; no representa un recibo generado por T03. Debe estar vinculada por el caller a la identidad/hash y decoder real del buffer. El flag `measured` aportado no certifica por sí solo medición. Los tests fabrican sólo `synthetic` identificado.

`BufferFacts = {buffer_id:Literal[parent_a,parent_b,engine,converted_b,converted_engine],sha256:SHA256,format:AudioFormat,frames:int,duration_s:float,measurement:MeasurementRef}`. `duration_s` exige type(value) is float (también excluye bool/int), debe ser finita, positiva, exactamente `float(frames/sample_rate)`; es representación derivada de los frames recibidos, nunca request. Desigualdad rechaza; no corrige el input. El parent master capturado exige SHA/rate/channels iguales y `asset.duration_s` exactamente igual a esta duración derivada. Si el caller sólo tiene duración aproximada, debe volver a medir antes de captura nueva; una receta ya sellada incoherente se rechaza, no se reescribe. ROOT ratificó esta política estricta para snapshots nuevos ligados a medición real; no toma duration deseada de requests ni reescribe recetas históricas.

`ParentFacts = {parent_id:ULID,asset_id:ULID,root_id:ULID,role:Literal[source,crossfade_a,crossfade_b],buffer:BufferFacts}`. Vinculación exacta contra parent snapshot, incluyendo root. Parent único usa `parent_a`; crossfade A/B usa `parent_a/parent_b`, en orden de receta. Ni faltantes, duplicados, swaps, extras o mezcla de propietario/song. T03 valida la raíz `min(parent.root_id)` contra recipe.root_id; el caller prueba que esas raíces son originales alcanzables según ADR-0041. El mínimo no se calcula sobre IDs de padres directos.

`EngineFacts = {recipe_sha256:SHA256,descriptor_sha256:SHA256,output_shape:Literal[full,region],buffer:BufferFacts,result:MeasurementRef}`. Buffer ID engine; todos los hashes/shape deben coincidir con executor inference sellado. CPU exige null; inferencia exige facts, exactamente una salida. No existe campo engine/attempt/seed/SQL en el plan que sustituya autoridad real. Variation_request/variation_audio/cover sólo permiten full, coherente T02.

### 4.2 Conversión explícita, anterior al cierre

Formato target: trim/fade conserva padre; crossfade conserva A tal como T02 selecciona. Extend/repaint usa formato del padre para dar coordenadas de construcción comparables. Variaciones/cover usa formato nativo de salida engine. No se solicita conversión del padre A ni trim/fade. Si B o engine difiere del target en rate o canales, se necesita su conversión completa antes del cierre final. Cambiar el formato target por preferencia del caller no está permitido.

`ConversionRequirement = {conversion_id:Literal[b_to_target,engine_to_target],input_buffer_id:Literal[parent_b,engine],input_sha256:SHA256,input_format:AudioFormat,target_format:AudioFormat,recipe_sha256:SHA256,tool:ToolSelection,channel_policy:Literal[identity,mono_to_stereo_duplicate,stereo_to_mono_average],resample_policy:Literal[identity,soxr_pinned]}`. Ambos formatos iguales no generan requirement. Tool es el único pin con tool_id=ffmpeg dentro de recipe.executor.tools; si falta, COMPOSITION_FACTS_REQUIRED; si se repite, COMPOSITION_INVALID. Selección y orden son deterministas. No se inventa un ejecutable, filtro libre o un pin nuevo. El caller requiere runtime real para ejecutar. Las políticas cerradas fueron ratificadas por ROOT; renderer convierte buffer completo sin normalizar/limitar.

`ConvertedFacts = {requirement:ConversionRequirement,buffer:BufferFacts,evidence:MeasurementRef,conversion_scope:FrameSpan}`. Buffer ID correspondiente converted_b/converted_engine, rate/channels target, frames medidos propios, hash propio y enlace al requirement exacto. `conversion_scope` exige exactamente `[0,input.frames)` de sus facts originales; no admite scope vacío, parcial ni otro buffer. No exigir distinto SHA por principio: validar identidad del buffer/facts y evidencia, no confundir igualdad de bytes con autoridad. No derivar `converted.frames` por ratio entre rates. Falta facts/evidence requeridos -> `COMPOSITION_FACTS_REQUIRED`. Facts extra/no necesarios, formato/pin/binding incorrecto -> rechazo.

La conversión consume todo el buffer original en su grid local. `conversion_scope` declara la dependencia completa, no el footprint exacto de soxr. El mapa nominal organiza el linaje; no promete contribución exclusiva de esas muestras. No restringe la duración total convertida a una estimación matemática; ese control de herramienta pertenece a T08 con referencia medida.

Cada operación comprueba sólo las coordenadas que utiliza. La región o el punto global de repaint/extend pertenece al padre, nunca al buffer local engine region. La conversión no vuelve a resolver esa región en engine ni en converted_engine.

| Operación/shape | Grid de intención | Grids de construcción y bounds |
|---|---|---|
| Trim/fade | Padre nativo, igual a target | Todos los spans dentro del padre; rampas target de al menos dos frames |
| Crossfade | D en A/target y B nativo | `D<=NA`, `0<D_B<=NB`, `D<=NBc`; rampa target mínima2; sin exigir sufijo nominal positivo |
| Repaint region | `[t0,t1)` global, resuelto sólo contra el padre target | Engine local nativo `[0,NE)` completo para conversión; construcción local `[0,G)` completa; no contiene `[t0,t1)` global ni exige G igual región eliminada |
| Extend region | at global, resuelto sólo contra el padre target | Engine local nativo `[0,NE)` y construcción local `[0,G)` completos; no exige at dentro del engine |
| Repaint full | `[t0,t1)` global, resuelto sólo contra el padre target | Construcción full local `[0,E)`; `E>i0+(N-i1)`; prefix/suffix colocados por esos counts target; entrada nativa de conversión completa |
| Extend full | at global, resuelto sólo contra el padre target | Construcción full local `[0,E)`; `E>a`; entrada nativa de conversión completa |
| Variaciones/cover full | Sin región del padre para construcción | Engine nativo completo `[0,E)`; formato target nativo; E positivo |

En full convertido, sólo los counts del buffer de construcción target determinan los splits de render. No se crean subspans nativos engine por ratio o por segundos globales. Sus facts nativos positivos y su scope completo conservan la entrada real. Una construcción demasiado corta para los keeps full y al menos un frame generado se rechaza. Region acepta una longitud local distinta de la región/punto del padre, sin clamp ni padding.

### 4.3 Resolución única: algoritmo, representación y límites

Se resuelven primitivas de operación, no se redondea cada `src/dst` ideal de T02 de manera independiente. Los destinos se construyen por sumas de frames ya resueltos. Se registra cada primitiva/grid y se reutiliza su resultado; el renderer no toma decisiones con segundos. Extremos reales de buffer son siempre 0 y N.

`round_frame(seconds,rate)` acepta int/float no bool, finito, >=0, y rate entero acotado. Normaliza a float como T02; overflow al convertir int se rechaza. Convierte el **decimal más corto de `repr(float(seconds))`** a racional exacto p/q, incluidos exponentes. Multiplica p por rate usando enteros; calcula `floor(p*rate/q+1/2) = (2*p*rate+q)//(2*q)`. No usa `round()`, producto float binario ni contexto Decimal con precisión implícita. Así 0.05 a 10 Hz -> 1 y 0.15 -> 2. `-0.0` cuenta como cero al resolver, pero no modifica bytes de receta. Producto exacto mayor que MAX_FRAMES o resultado fuera de rango -> `COMPOSITION_LIMIT_EXCEEDED`. El límite se comprueba antes de convertir a índice C; operaciones no requieren memoria proporcional.

Límites temporales contra buffer: un valor igual al `duration_s=float(N/rate)` de sus facts representa explícitamente el extremo medido y resuelve N; esto evita rechazar una representación float de N/rate por sus últimas cifras. Cualquier otro valor se compara como racional decimal exacto contra N/rate y se rechaza si está fuera, incluso si el redondeo habría dado N. No saturar. `round_frame` aislado no tiene este anclaje: lo aplica `resolve_region` con facts.

`BoundaryResolution = {key:Literal[trim_start,trim_stop,repaint_start,repaint_stop,extend_at,fade_in_length,fade_out_length,crossfade_length],buffer_id:BufferId,seconds_decimal:str,rate:int,frame:int,anchor:Literal[decimal_half_up,buffer_start,buffer_end]}`. `seconds_decimal` es repr del float sellado, sin input libre ni rutas; máximo 32 caracteres, decimal/exponente válido y finito. Cero puede anclarse a buffer_start. Se usa una entrada por clave/buffer y ninguna repetida. Es testigo de resolución, no otra intención editable. A B convertida le corresponde su propia entrada de D a target rate; a B original otra a su rate.

Trim/repaint resuelve extremos contra fuente; región positiva en segundos que colapsa a `i0>=i1` falla. Extend permite índice 0 o N y omite keep vacío. Fade/crossfade resuelve duración; duración positiva que redondea a 0 falla. Rampas de **una muestra se rechazan** `COMPOSITION_ENVELOPE_TOO_SHORT`: política v1 exige al menos dos frames; no inventa división por cero ni un singleton arbitrario. Fades de entrada/salida usan 0..Fin y N-Fout..N; cada duración se resuelve una vez, suma Fin+Fout<=N. Centro cero se omite; no genera mapas vacíos.

Crossfade D en target grid usa A y debe cumplir D<=A.frames y D<=B_construction.frames. En native B también se resuelve D_B y comprueba 0<D_B<=B.frames. A empieza su cola en `A.frames-D`, no por redondeo independiente de `duration_s-D_s`. B termina solape en D, resto hasta sus frames medidos. Esta regla de extremos anclados impide divergencias de una muestra entre overlap y duración total. Regiones en grids distintas nunca se comparan como números de índice sin rate.

### 4.4 Forma cerrada del plan y mapas por arista

`CompositionPlanV1` tiene exactamente:

```text
kind: Literal[creative_composition]
schema_version: Literal[1]                 # entero exacto
recipe_sha256: SHA256
operation: Literal[variation_request,variation_audio,extend,repaint,cover,trim,fade,crossfade]
root_id: ULID
output_shape: Literal[full,region] | null  # null para CPU, copia comprobada de selection para engine
descriptor_sha256: SHA256 | null          # null para CPU
status: Literal[resolved_unrendered]
target_format: AudioFormat
inputs: tuple[ParentFacts,...]            # 1 o 2, orden sellado
engine: EngineFacts | null
conversions: tuple[ConvertedFacts,...]    # 0 o 1 en operaciones actuales
resolutions: tuple[BoundaryResolution,...] # 0..12, orden key de operación/grid semántico fijo
pieces: tuple[RenderPiece,...]            # 1..3, partición exacta del destino
edges: tuple[ResolvedEdgeMap,...]         # 1 o 2, por padre/rol
output_frames: int                       # >0, calculado de frames aportados
output_duration_s: float                 # float(output_frames/target_rate), no request
```

`CapturedCompositionPlan = {value:CompositionPlanV1,payload:bytes,sha256:SHA256}` es wrapper congelado, Su SHA corresponde a los bytes canónicos del plan; recipe_sha256 corresponde a los bytes de la receta. Son dominios tipados separados. No se exige desigualdad universal de sus hashes ni se usa igualdad/desigualdad como prueba de autoridad, ejecución o transformación. No contiene execution_id, ruta, autoridad de publicación, timings reales o recibo terminal. La duración de plan procede de longitudes medidas de buffers/primitivas resueltas; todavía no es una medición de audio renderizado. T08 mide la salida y debe comprobar su frame count exacto contra el plan. Una tolerancia de duración decodificada ±1 sample del test-plan no permite modificar mapas o ensamblado después de sellarlos.

`RenderPiece = {kind:Literal[copy,fade,crossfade],dst:FrameSpan,terms:tuple[RenderTerm,...]}`. `RenderTerm = {buffer_id:BufferId,span:FrameSpan,envelope:Literal[identity,linear_in,linear_out]}`. Copy tiene un término identity; fade un término in/out; crossfade dos términos ordenados A out/B in. Cada término tiene longitud igual a dst, sólo buffers de construcción con formato target; rango dentro de sus facts. Las piezas copy de longitud cero se omiten antes de construir spans; terms tiene exactamente 1 término en copy/fade y 2 en crossfade. Pieces ordenadas, adyacentes, desde 0 hasta output_frames sin gaps/overlaps; sólo los términos de crossfade se mezclan. No nodos, índices de pieza editables, loops, comandos, filtros libres ni fuentes desconocidas.

Envolvente candidata v1: para K>=2 y n=0..K-1, linear_in=n/(K-1), linear_out=1-linear_in. Complementarias exactamente como fórmula racional; el renderer fija precisión de cálculo. Se aplica el mismo gain en ambos canales. T03 describe, T08 mide el resultado con herramientas fijadas, incluyendo true peak tras conversión y umbrales del test-plan. No acredita clipping ni preservación PCM.

`ResolvedEdgeMap = {kind:Literal[resolved_frames],parent_id:ULID,role:ParentRole,source_format:AudioFormat,destination_format:AudioFormat,source_frames:int,destination_frames:int,ops:tuple[ResolvedMapOp,...]}`. IDs/roles/formats/cuentas iguales a facts y plan, exactamente una arista por padre. No incluye child_edge_id SQL. Cada op tiene exactamente:

```text
op: Literal[keep,fade,regen,append,convert]
effect: Literal[keep,fade,regen,append] | null
src: FrameSpan | null                     # fuente directa o conservación declarada del padre
nominal_src: NominalFrameRange | null      # sólo B convertido; no es fuente literal ni footprint del filtro
dst: FrameSpan                            # coordenadas destino target
render_buffer_id: BufferId
render_span: FrameSpan                    # fuente real que consume renderer
conversion_id: Literal[b_to_target,engine_to_target] | null
envelope: Literal[identity,linear_in,linear_out]
claim: Literal[direct_copy,transformed,generated,declared_keep_unverified]
```

Todas las claves de la op son obligatorias, incluidas `src` y `nominal_src` nullable. La combinación op/effect/conversion/buffer/claim determina su variante cerrada:

| Variante | src | nominal_src | Binding/claim |
|---|---|---|---|
| Keep/fade sin conversión | FrameSpan del padre | null | effect/conversion_id null; claim según construcción directa o full declarado |
| Regen/append sin conversión | null | null | effect/conversion_id null; generated |
| Convert B, effect keep/fade | null | NominalFrameRange obligatorio del padre B | b_to_target, converted_b, transformed; scope completo de B |
| Convert engine full, effect keep | FrameSpan conservado declarado del padre | null | engine_to_target, converted_engine, declared_keep_unverified; scope completo engine |
| Convert engine, effect regen/append | null | null | engine_to_target, converted_engine, generated; scope completo engine |

No hay convert engine/effect fade en estas operaciones. Tampoco keep/fade de B convertido con src literal ni variantes con ambos campos no-null. Cualquier tramo que usa converted buffer exige op convert; `effect=keep` no significa keep puro. Para keep/fade sin convert, src y dst tienen igual longitud/formato. Cada `src` no-null está dentro del master original de la arista; no se usa como coordenada del engine full.

Crossfade B convertido construye exactamente dos candidatos nominales: fade `[0,D_B)` y keep `[D_B,NB)`. El rango usa source_format/source_frames de B original, nunca el formato/count de Bc. El fade conserva la restricción `0<D_B<=NB`; el keep admite `D_B=NB`. Una op sólo se emite si su render_span/dst es no vacío. Si `D=NBc`, se omite el keep aunque exista rango nominal nativo restante. Si `D<NBc` y `D_B=NB`, se conserva keep con nominal_src `[NB,NB)`, render Bc `[D,NBc)` y dependencia `[0,NB)`. No inventa vecinos ni recorta frames medidos. El nominal vacío procede de extremos resueltos exactos; no de clamp.

La validación/replay rechaza rango nominal fuera de B, invertido o distinto de la fórmula, y scope distinto del buffer original completo. Rechaza nominal_src fuera de la variante B convert, src literal en esa variante, y spans vacíos de render/destino. Los bounds inválidos son `COMPOSITION_OUT_OF_BOUNDS`; combinaciones/fórmulas/scope inválidos son `COMPOSITION_INVALID`. Una cola nominal vacía válida nunca produce `COMPOSITION_INTERVAL_COLLAPSED`.

`render_buffer_id/render_span` son verdad de construcción. En region el keep usa parent buffer y claim direct_copy; en full puede declarar keep pendiente con render buffer engine y claim declared_keep_unverified. Un keep full nunca afirma copia exacta del padre. Fade/convert usa claim transformed; regen/append generated. Para full convertido, los keeps pasan a convert/effect=keep con claim declared_keep_unverified; generados a convert/effect=regen/append. Sólo T08, tras comparar regiones padre/salida en formato común, puede emitir un recibo efectivo que confirme o rechace esas regiones. Un full que cambió el prefijo falla su gate de preservación; no se reclasifica como keep demostrado ni se sustituye por copia de padre a escondidas.

Ops tiene 1..3 elementos; keep/regen/append exigen envelope identity, fade linear_in/out, convert la envolvente correspondiente a effect. Los mapas mantienen orden cronológico por padre. El destino se particiona para padre único; crossfade permite overlap **entre aristas** exclusivamente en los fades complementarios, conservando ambos roles. `source_frames` siempre cuenta el master original, no el buffer convertido. `destination_frames` igual output_frames. No usar `requested_seconds` como este formato ni publicar estos mapas privados en schema histórico de datos que aún sólo enumera cuatro ops. T07/T04 deberá concretar/probar proyección que represente convert explícitamente, sin degradarlo a keep; queda fuera T03.

### 4.5 Reglas exactas de composición

| Operación/shape | Fuentes de render y longitudes | Mapas de construcción/procedencia |
|---|---|---|
| Trim | Parent[i0,i1); Nout=i1-i0 | source keep [i0,i1)→[0,Nout), copia intencional directa |
| Fade | Parent completo; Nout=Nparent; fades y keep central según Fin/Fout | source fade/keep/fade, omitiendo centro cero |
| Crossfade | Copy A[0,NA-D); mix A[NA-D,NA) + Bc[0,D); copy Bc[D,NBc); Nout=NA+NBc-D | A keep/fade; B fade/keep o convert effect fade/keep, ambas aristas |
| Repaint region | Copy parent[0,i0), engine_construction[0,G), copy parent[i1,N); Nout=i0+G+N-i1 | keep prefijo, regen G, keep sufijo desplazado por G-(i1-i0) |
| Repaint full | Única copy engine_construction[0,E); G=E-i0-(N-i1)>0 | keep padre[0,i0)→[0,i0) pendiente; regen→[i0,i0+G); keep padre[i1,N)→[i0+G,E) pendiente |
| Extend region | Copy parent[0,a), engine_construction[0,G); Nout=a+G | keep prefijo; append→[a,a+G); sufijo original descartado |
| Extend full | Única copy engine_construction[0,E); G=E-a>0 | keep padre[0,a)→[0,a) pendiente; append→[a,E) |
| Variaciones/cover full | Única copy engine[0,E) nativo; Nout=E | regen source null→[0,E), antecedente de su único padre |

Bc es B convertido medido si hace falta, o B nativo. E/G usan counts del buffer engine de construcción, convertido si hizo falta. Nunca duration deseada del request ni duración de región eliminada para inventar longitud nueva. Región válida puede cambiar duración; desplazamiento del sufijo se calcula de G real. Full requiere suficiente E para sus partes conservadas más **al menos un frame** generado. No deduce shape de la longitud. Region siempre consume toda su salida; full siempre consume toda la suya una vez. El descriptor/hash/shape recibido incompatible con receta falla, no adapta la receta.

La pieza render copy de un engine full no equivale a un lineage keep de todo el padre: son representaciones distintas. T08 contrasta los keeps declarados y las uniones; la obediencia real del modelo conserva sus gates humanos T12/T13.

### 4.6 API pura, reader y errores

```text
conversion_requirements(recipe: CapturedRecipe, *, parents: tuple[ParentFacts,...], engine: EngineFacts | None) -> tuple[ConversionRequirement,...]
round_frame(seconds: int | float, sample_rate: int) -> int
resolve_region(region: tuple[float,float], facts: BufferFacts) -> tuple[int,int]
build_composition_plan(recipe: CapturedRecipe, *, parents: tuple[ParentFacts,...], engine: EngineFacts | None, converted: tuple[ConvertedFacts,...]) -> CapturedCompositionPlan
read_composition_plan(payload: bytes, *, expected_sha256: str, recipe: CapturedRecipe) -> CapturedCompositionPlan
composition_bytes(plan: CapturedCompositionPlan | CompositionPlanV1) -> bytes
composition_sha256(plan: mismos tipos) -> str
```

Preflight no resuelve índices y no devuelve un plan parcial listo para render. Build vuelve a validar requirement/facts sin volver a producir redondeos temporales ya compartidos. Recipe wrapper se revalida a través de reader T02 con sus bytes/hash; un wrapper construido manualmente con value/payload discrepantes no cruza el borde. DTO wrappers no son una autoridad por el nombre de clase.

Codec igual a captura T02: UTF-8, ensure_ascii=False, sort_keys=True, separators compactos, allow_nan=False; no BOM/newline/NFC. Límite 1MiB, profundidad20 y256 elementos por colección; ni truncado ni números no finitos. El reader rechaza claves duplicadas, bytes no canónicos, hash distinto, kind/version desconocidos o mal tipados. Sólo entiende creative_composition/v1; no interpreta planes M1/PostPlan/recibos como legacy. Versiones anteriores M1 siguen en sus readers propios. No dispatch por parecido estructural.

El reader verifica recipe_sha y reconstruye el plan esperado mediante el builder a partir de sus facts ya contenidos; compara bytes canónicos completos. Este replay puro valida mapa/pieces/root/resolution tampered sin ejecutar audio. Los índices se recomputan únicamente al verificar lectura/replay, nunca para decidir el render de un plan ya leído; cada construcción/replay mantiene una sola resolución por key/grid. Hash garantiza integridad relativa a SHA externo, no autorización/custodia.

`CompositionError(ValueError)` sólo expone `code:str` de tabla y `field:str|null` de rutas estructurales conocidas e índices decimales; mensaje sólo código, sin repr/payload/contexto Pydantic, paths, letra o claves dinámicas. Romper cause/context chain como T02. No agrega HTTP/ErrorDTO en T03; integración futura mapea esos códigos.

| Code | Casos |
|---|---|
| COMPOSITION_INVALID | Tipos, bool, extras, no finitos, negativos, duplicados, forma/mapas/pieces |
| COMPOSITION_VERSION_UNSUPPORTED | kind/schema desconocidos o versión no int exacto |
| COMPOSITION_HASH_MISMATCH | Payload, recipe, source SHA o descriptor SHA discrepante |
| COMPOSITION_CONTEXT_MISMATCH | parent/asset/root/role/formato de snapshot o shape/executor incoherentes |
| COMPOSITION_FACTS_REQUIRED | Engine/medición/conversión requerida ausentes |
| COMPOSITION_DURATION_MISMATCH | duration_s no corresponde a frames/rate o snapshot capturado discrepa |
| COMPOSITION_OUT_OF_BOUNDS | Punto/región/duración fuera de facts; nunca clamp |
| COMPOSITION_INTERVAL_COLLAPSED | Región positiva en segundos queda vacía, duración redondea a cero o G<=0 |
| COMPOSITION_ENVELOPE_TOO_SHORT | Fade/crossfade de exactamente un frame |
| COMPOSITION_LIMIT_EXCEEDED | Bytes/depth/collection o aritmética fuera del límite fijado |

Orden determinista de validación: estructura/límites; hash/recipe; bindings/contexto; facts/duraciones; requirements/conversión; resolución/rangos/rampas; construcción/invariantes globales. Tests mezclados no deben depender de una precedencia no documentada.

### 4.7 Controles sintéticos exactos y aceptación antes de render

Los ejemplos son deducciones aritméticas documentales, **no ejecuciones de producto, mediciones reales ni recibos de audio**. Baseline A: rate10/channels2/frames100/duration10.0; B: rate10/channels2/frames80/duration8.0; G/E según fila. Todos los IDs/hashes/evidence que un test use serán fixtures synthetic, no resultados publicados.

| Control | Inputs/primitivas | Resultado exacto de plan |
|---|---|---|
| C01 Trim | [2.05,7.15] segundos | i0=21,i1=72; salida51 frames/5.1s; keep[21,72)→[0,51) |
| C02 Fade | in1.05,out2.05 | Fin11,Fout21; fade[0,11),keep[11,79),fade[79,100); salida100 |
| C03 Crossfade | D2.05 | D21; A keep[0,79),fade[79,100); B fade[0,21)→[79,100),keep[21,80)→[100,159); salida159/15.9s |
| C04 Repaint region | [2,4),G25 | i0=20,i1=40; piezas A[0,20),engine[0,25),A[40,100); dst[0,20),[20,45),[45,105); salida105/10.5s |
| C05 Repaint full | [2,4),E105 | Única pieza engine[0,105); regen[20,45); sufijo[40,100)→[45,105) pendiente; salida105 |
| C06 Extend region | at7,G40 | a70; A[0,70)+engine[0,40); salida110/11s; append[70,110) |
| C07 Extend full | at7,E110 | Única pieza engine[0,110); keep[0,70) pendiente; append[70,110); salida110 |
| C08 Extend end/zero | at10,G40; at0,G40 | end salida140, keep[0,100),append[100,140); zero salida40, sólo append |
| C09 Repaint all | [0,10),G25 region/full | salida25; sólo regen, sin keeps vacíos; full/region cada una una fuente engine |
| C10 Convert B | B rate20/ch1/N160; Bc rate10/ch2/N81 medidos; D2 | native D_B40; converted D20; output161; B ops convert src null, effect fade nominal_src[0,40)→dst[80,100),keep nominal_src[40,160)→dst[100,161); conversion_scope[0,160) |
| C11 Root dual | raíces originales …003 y …001; direct parent IDs …000 y …999 | root…001; aristas A/B ambas; nunca min direct IDs |
| C12 Cola convertida B01 | A100@10; B160@20; Bc81@10; D8s | D80,D_B160; A keep[0,20),mix dst[20,100),Bc keep[80,81)→dst[100,101); B convert/effect keep src null,nominal_src[160,160),conversion_scope[0,160); salida101 |
| C13 Región local B02 | Padre100@10; repaint global[6,8); engine region40@20 convertido20@10 | i0=60,i1=80; engine nativo local[0,40),construcción local[0,20); piezas padre[0,60),Bc_engine[0,20),padre[80,100); dst[0,60),[60,80),[80,100); salida100 |

Matriz candidata de tests futuros. Cada fila negativa requiere su control válido pareado y excepción segura sin datos. No se han ejecutado los nombres propuestos.

| AC | Negativo/control y aserción necesaria | Traza |
|---|---|---|
| AC01 | C01/C02; trim vacío/invertido/negativo/out-of-bounds/fade sum>N rechazados; frames y piezas exactos | CA-13/14 |
| AC02 | 0.05@10→1,0.15@10→2; float y exponentes; no round ties-even ni float product; signed zero preserva recipe | CA-13/14/15 |
| AC03 | [0.01,0.02]@10 colapsa; D0.01 colapsa; in0.1@10 y cross0.1@10 singleton fallan; 0.2@10 rampa2 pasa | CA-13/14/15 |
| AC04 | bool en rate/channels/frames/version/tiempos; strings/Decimal; NaN/±inf; frames0/negative; duration no finita; control tipos exactos | CA-13 |
| AC05 | Limite frames2**63-1 aceptable para DTO sin materializar audio; MAX+1,rateMAX+1,secs1e308 y suma overflow fallan; input gigante falla sanitizado | CA-13 |
| AC06 | facts duración distinta a N/rate, snapshot stale, hash/asset/parent faltante o swap rechazados; C01 consistent pasa | CA-13/14/15 |
| AC07 | endpoint igual duration derivada N/rate se ancla a N; `nextafter(duration,+inf)` se rechaza aunque redondee N; fuera bounds no clamp | CA-13 |
| AC08 | C03 ambos roles/maps/rates/channels/root; falta B, inversión roles/roots, canciones distintas en recipe falla T02; mínimo raíces no mínimo padres | CA-15 |
| AC09 | C10/C12 conversion necesaria sin facts/evidence/pin o wrong target falla; facts extra/no necesaria falla; B convert nunca keep puro; nominal nativo distinto de render/dst target; nominal_src en variante indebida, src literal convertido, nominal invertido/fuera bounds o scope parcial fallan | CA-13/15 |
| AC10 | C12 cola Bc positiva/nominal vacío aceptada con dependencia completa; Bc80 omite cola; Bc79 con D80 falla bounds; D_B160 extremo válido; D_B>160 falla; frames81 aportados no estimados80; policy canales identity/duplicate/average exacta; dst/render vacíos fallan | CA-13/15 |
| AC11 | C04 vs C05 mismos105frames y distintos pieces; C13 acepta región global[6,8) con buffers locales2s; región fuera del padre falla; region G distinto aceptado; full E<=80 deja regen<=0 y falla, E81 acepta1frame generado | CA-11/13 |
| AC12 | C06 vs C07 mismos110frames; full no parent copy ni doble ensamblado; shape mismatch/hash descriptor mismatch/facts engine en CPU faltantes o extra fallan | CA-09/11/13 |
| AC13 | C08/C09 omiten keeps vacíos; extend full E<=a falla; region salida positiva aun cuando at0; duration derivada jamás params duration deseada | CA-09/11/13 |
| AC14 | Full keeps claim declared_keep_unverified, fuente engine; region keep direct_copy fuente padre; plan status unrendered y ausencia de flags fidelity/clipping/pass de audio | CA-09/11/14 |
| AC15 | Recipe payload/hash/descriptor idénticos before/after build/read; mutar input/list/model_dump/views no altera plan o receta; DTO nested frozen | CA-09/11/14/15 |
| AC16 | Codec/replay idéntico, dominios kind/version separados y SHA de sus propios bytes, sin exigir desigualdad de hashes ni evidencia de autoridad por igualdad/desigualdad; tamper resolutions/map/pieces/frames/parent/claim/version/extras/duplicatedJSON/noncanonical rechazo | CA-13/15 |
| AC17 | Build/preflight puro sin imports directos de audio/GPU/subprocess/SQL ni llamadas read/write o side effect; imports transitivos actuales de T02 no autorizan consultas ni I/O; buffers synthetic no habilitan runtime; tests no crean job/attempt/take fake | CA-14 |
| AC18 | Error sólo code/field permitidos, cause/context sin input/paths/letra/secret; raw Pydantic repr no escapa; reader M1 nunca invocado ni cambiado | CA-13 |

Traceabilidad E2E-04→AC11–13 (extend); E2E-05→AC11/12/14 (repaint); E2E-07→AC01–10/15–18 (CPU). Estos son tests focales puros; no sustituyen E2E ni la ejecución real del renderer ni aceptación musical/humana. La verificación de tarea futura sigue siendo `uv run pytest -q apps/server/tests/test_creative_composition.py`, con RED y puertas de review/QA/cobertura del ledger. Este actor no la ejecuta en fase de propuesta documental.

## 5. Impacto en módulos y ficheros

| Ruta real | Responsabilidad futura |
|---|---|
| `apps/server/app/creative/composition.py` | Nuevos DTO/helpers/plan/readers puros; archivo nuevo propuesto, sin implementación aquí |
| `apps/server/tests/test_creative_composition.py` | RED focal y controles/negativos de la matriz, archivo nuevo propuesto |
| `apps/server/app/creative/recipes.py` | Consumido por API existente T02; contrato/bytes preservados |
| `docs/arquitectura/iteracion-creativa.md` | ROOT/implementer documentará seam y estados reales al ratificar, no escrito aquí |
| `docs/roadmap/2026-10-10-m2-iteracion-creativa/recipe-contract-design.md` | Fuente T02 §4.7; no sustituir sus mapas de intención |
| `docs/roadmap/2026-10-10-m2-iteracion-creativa/cpu-contract-design.md` | Futuro enlace por ROOT; composición no es CpuEditPlan/publicación durable |
| `docs/arquitectura/datos.md` | Futuro contrato explícito para convert al publicar; no cambia en T03 puro |

T08 hace prepass conversion/medición y render, contrasta keeps/true peak/tolerancias y conserva recibo propio. T07 incorpora plan SHA/facts/mapas efectivos a autoridad y publicación ya diseñada; no llama a M1 con campos engine falsos. T11–T14 aportan resultado/shape verificados y reutilizan builder; no inventan otro ensamblador ni infieren shape por nombre/modelo. Toda decisión duradera posterior corresponde a ROOT, con ADR si cruza umbral.

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Metadatos T02 con duración aproximada | Política estricta de facts; re-medir antes de captura, rechazar receta stale sin reescribir. ROOT ratificó política; review/QA del contrato preceden al RED |
| Conversiones requieren orden prepass→cierre→render | Preflight sin índices, facts convertidos medidos; contrato final no permite pendientes ni frames por ratio |
| Cola convertida sin intervalo nominal nativo positivo | NominalFrameRange admite igualdad sólo en nominal_src de B convertido; render/destino no vacíos y conversion_scope completo conservan frames y dependencia |
| Mezcla de región global del padre y salida local engine | Tabla de grids/bounds por operación; region consume buffer local completo; full valida sólo sus splits target |
| Full pretende preservar algo que el engine cambió | Claim explícitamente unverified; renderer compara PCM y falla gate, sin ensamblar padre de nuevo |
| Convert privado aún no cabe en mapas históricos | No publicar DTO privado; T07/T04 concreta schema honesto y prueba proyección antes de integración |
| Fact/evidence válido estructuralmente pero falso | Caller verifica bytes y custodia; refs sintéticas nunca reemplazan evidencia runtime |
| Re-redondeo en renderer/replay divergente | Renderer sólo consume frames; reader replay compara determinísticamente bytes de algoritmo v1 |
| Crossfade puede clippear pese a gains complementarios | Medición T08 posterior a conversión; umbral test-plan; ninguna prueba de clipping en T03 |
| Rampa singleton sin semántica fijada | Rechazo explícito mínimo2frames; no cambia request ni fuerza duración silenciosamente |

## 7. Preguntas abiertas y evidencia de preparación

ROOT eligió O1 y ratificó duración exacta frames/rate medidos, rampas de al menos dos frames, target padre en extend/repaint, conversión completa y keeps full declarados. La política de hashes valida cada dominio por sus bytes y no exige desigualdad. FIX1 propone separar nominal_src nullable/posiblemente vacío de src/render spans estrictos y persistir conversion_scope completo. Esa representación necesita ratificación de ROOT antes de producto; no se presenta como política ya aprobada.

La precisión de grids por shape y los controles C12/C13 resuelven los contraejemplos documentales sin modificar T02. Permanecen revisión documental y QA del contrato, incorporación por ROOT y las evidencias reales futuras. Este actor no autoaprueba diseño/ADR ni habilita producto.

No hay faltante de contexto que impida formular O1. La proyección publicada de convert y el CpuEditPlan/recibo durable aún no se fijan aquí: son fronteras T04/T07 ya delimitadas, no se deben inventar para cerrar T03. Si ROOT exige que T03 publique linaje, se necesita cambiar el scope antes de RED.

La preparación original conserva guards-selected-before/after y su recibo de selección. FIX1 se limita a tres documentos del snapshot enumerados en release-root.receipt.json y a report.md/receipt.json propios. Sus guardas comprueban las 26 fuentes antes/después y el alcance exacto de tres cambios. No escribe canon/Git/ledger/CONTINUE/locks/meter/código/tests/audio/servicios; conserva review1 original intacto.

La revisión de interfaz verificó en recipes.py que ToolSelection tiene tool_id, lock_sha256, revision, archive_sha256, recipe_revision, license, commercial_use y runtime_verified; ambas selections contienen tools, inference contiene descriptor_sha256/output_shape y CPU contiene output_format. La fixture T02 usa tool_id=ffmpeg y runtime_verified=false; es coherencia sintética, no aprobación de instalación/licencia/capacidad real. T03 referencia el pin exacto, no inventa un campo de soxr. La presencia de FFmpeg/soxr en locks no acredita licencia vigente ni soporte runtime; T08 debe verificarlos antes de ejecutar. El actor no consultó red ni ejecutó esas herramientas.

Comprobación documental FIX1: siete secciones, ningún placeholder/comentario guía, 13 controles y 18 AC, opción O1 elegida, estado borrador y ADR propuesta. report.md/receipt.json registran controles aritméticos, hashes y límites propios. Ningún recibo de ejecución, RED, producto o audio se fabrica. ROOT hará ratificación/revisión documental/QA antes de incorporar o autorizar el RED.


## Ratificación contractual de ROOT — 2026-10-11T14:46:46.675900+00:00

O1 y representaciónnominal/conversion_scope adoptadas tras revisión2A/B0gaps y QA documental60/60. ProductoT03/TDD/render/audio/E2E pendientes; no se reescribe T02 ni historia.
