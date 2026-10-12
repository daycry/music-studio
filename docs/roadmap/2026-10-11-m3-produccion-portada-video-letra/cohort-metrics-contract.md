---
documento: cohort-metrics-contract
titulo: D-06 y D-13 — cohorte independiente, métricas y evidencia
estado: propuesta
fecha: 2026-10-12
version: 1
adopcion: CM-O1 recomendada; ratificación ROOT por SHA pendiente
---

# Contrato D-06/D-13

Este candidato concreta T-06 y E2E-04/M-17/21/25/28/29/31/33/43/49. La preparación normativa no termina T-06: faltan ratificación, personas/material/anotaciones reales y el instrumento `scripts/m3_coverage_gate.py` con RED causal, GREEN, raw oficial, revisión y QA. **TDD n/a: prosa contractual.** Los casos documentales no son medición musical, cobertura de producción ni conformidad CPU/GPU. El objetivo delegado sigue M0–M5; aquí no se cambia ni reduce ese objetivo.

## 1. Decisión concreta, límites y congelación

| Opción | Decisión | Coste/riesgo y reversibilidad |
|---|---|---|
| CM-O1, recomendada | Dos anotadores independientes por ítem; árbitro distinto para discrepancias; aceptación por canción/método y acta humana; rúbrica numérica §5 | Mayor tiempo humano; reduce sesgo y admite ambigüedad explícita. Nuevo perfil versionado si cambia, sin reescribir anotaciones |
| CM-O2 | Un anotador independiente y segundo revisor del 100 % del audio, con discrepancias archivadas; mismos límites numéricos | Menor paralelismo humano; riesgo de anclaje al primer anotador. Requiere decisión ROOT previa; no equivale a CM-O1 |
| CM-O3 | CM-O1 con límites más estrictos: palabra 0,075/0,200s; beat 0,050s/F1≥0,95; sections 0,500s/F1≥0,90; key≥0,95 | Mayor coste/posible abstención. Son propuestas del proyecto, ninguna norma musical. No elegir después de ver resultados |

ROOT elige opción y ratifica **todos** los valores/políticas del perfil, no sólo 100/250ms. `production.cohort_freeze/1` captura bytes/SHA del contrato, rúbrica, cohorte, referencias, identidades cegadas de personas y pin de cada método antes del primer RED dependiente. La instrumentación de cobertura requiere revisión del contrato y su propio RED; no espera conformidad musical para empezar. Un método musical necesita D06 ratificado antes de su RED; su evaluación real necesita además D13 adquirido. Una propuesta congelada es revisable, pero no es adopción. Cambio tras resultados crea revisión nueva, conserva la anterior y exige evaluación nueva; no recalifica retrospectivamente.

No se accede aquí a medios privados, GPU, servicios, SDK, downloads, pesos, herramientas o licencias nuevos. La declaración disponible es **letra propia Libre**; no acredita derechos de audio, imagen, persona, biblioteca o comparación. Un MP3 aportado para comparación no concede autorización general, derechos comerciales, consentimiento ni permiso para entrenar/editar/publicar. Ningún consentimiento, autoría, anotación o firma se inventa. Material no admitido permanece fuera de cola y cohorte evaluable.

## 2. Fuentes exactas y compatibilidad

El corte pertenece a `release-root.receipt.json.readonly_snapshot_sha256`, 141 pins de sólo lectura; fuente nueva owned inicialmente ausente. Antes de escritura se compararon los pins por SHA sin diferencias. La autoridad es el SHA de este release, no tablas históricas citadas dentro de sus fuentes.

| Fuente | SHA-256 vigente en este corte |
|---|---|
| production-request-contract.md, D-02 | 94e4c84771084b469bca1064dee78595930d075ed31ef13877166bed54eeb530 |
| production-data-contract.md, D-03 FIX1 | ca094b156a538467b495804899e5a21aff917113b44728df9ab88fbf92e76f13 |
| production-format-contract.md, D-04 | cf967985d01f102a908ddd0c9658d59985156aafffc47691abc71e9995e56c83 |
| audio-measurement-contract.md, D-05 | 156086989bb2bcd4eaf052f43ea9520026ed2163fac92eedc7575e079c46eac8 |
| tasks.md | 3345ea2945737c768839ea1b012e4dd4fad3e257862a5be1e7be61d9b23169c2 |
| test-plan.md | fe76ac3f78983a36f4efabf98efa85eee9b97593574ea3095f895d5bc5f45855 |

D-02 mantiene sus 19 parejas/7 sujetos y ProductionRequest1/Recipe1/Receipt1. D-03 mantiene 40 tablas, 11 familias internas y `seal_kind`; D06 **no** añade `seal_kind` a payloads externos. `m3_analysis_result.method` sigue beats/sections/key/loudness/lyrics_timing y `outcome` sigue succeeded/failed/missing; ningún outcome SQL `uncertain`, `not_requested` o `indeterminate` nuevo. D-04 mantiene CapturedRef/ByteRef/RevisionRef/ProfileRef y TimelineV2/SceneN01, sin nuevas propiedades. No se cambia Analysis UNIQUE, Asset enums, DTO M1, engine `/v1`, manifest/song v1/CPUv2 ni bytes históricos.

Los readers nuevos siguientes son nombres propuestos para implementación code-first futura; registro exige schema/código/goldens/SHA liberados conjuntamente. Unknown/version desconocida falla antes de efectos. D03 `production.analysis_result/1` conserva su envolvente y refiere un payload de método de §4. Una ejecución correcta que abstiene puede tener outcome succeeded y payload state=indeterminate, sin promesa de capacidad; fallo real usa failed/data NULL; sin ejecución solicitada válida usa missing/data NULL. Error_code procede de D02/D03, no se añade enum al envelope. Loudness consume **exactamente** `production.audio_measurement/1` y `production.audio_measurement_profile/1` de D05, sin duplicarlos. Una captura textual de sections mantiene origin=textual; nunca cuenta como ground truth ni medición musical.

## 3. Cohorte privada, derechos, personas y referencia independiente

Raíces futuras privadas dentro del proyecto: `eval/m3/cohorts/<cohort_id>/`, `eval/m3/annotations/<cohort_id>/`, `eval/m3/evidence/<run_id>/`. No se crea ninguna de estas aquí. Catálogo público sólo IDs opacos, contadores y hashes sanitizados: sin letra, audio, fotos, nombres, paths personales o secretos. El hash no es licencia ni prueba de origen. Resolución de refs privada autenticada valida propietario/custodia/permisos actuales; revocación bloquea nuevos usos sin reescribir capturas históricas.

CM-O1 propone al menos **8 canciones completas** cantadas en castellano, incluida Libre4:15 (255s nominales; duración efectiva obligatoriamente medida N/Fs). Se planifican cupos, no se fabrican ítems: al menos 2 con omisiones, 2 con repeticiones, 2 con silencios/instrumentales, 2 con más de180s; pueden coincidir y cada rasgo exige anotación real. Diversidad de tempo, densidad de canto y forma, dos tasas y mono/estéreo donde realmente disponibles; no convertir para inventar diversidad. Si la cohorte real no cumple cupos, state=blocked y falta enumerada, sin extrapolar. Cada caso íntegro conserva [0,N/Fs), EOF, colas y silencio, sin evaluación limitada a180s ni recorte favorable. Las métricas se publican por canción y estrato; no aceptar sólo promedio de cohorte.

Subcohortes separadas: `music` (alineación/análisis/F19/calidad), `artwork` (generación y referencia consentida como gates distintos), `full_render` (cada canción completa, ambos perfiles requeridos), `backup_recovery` (copia de biblioteca real autorizada). Derechos para una subcohorte no se extienden a otras. F19 requiere audio propio autorizado y caso real reconocible; MP3 comparador no suplanta input autorizado de producto.

Personas propuestas, aún **sin asignar**: anotador A, anotador B, árbitro independiente C y revisor perceptual R. Asignación necesita ID opaco, aceptación explícita, función y declaración de independencia. A/B no son autores del resultado evaluado ni ven outputs, timestamps, confianza, tags/sections del modelo; sólo fuentes autorizadas y reglas. La escucha A/B de calidad es ciega y orden aleatorio registrado. C ve dos anotaciones después de su freeze, no output evaluado. R puede ser una persona ya asignada si no juzga su propia salida y se declara el conflicto; CA21 utilidad/CA25 visual/CA28 reproducción/CA31 F19/CA33 calidad requieren actas de revisión específicas. Nadie está asignado ni firma aquí. Independencia significa separación real de resultados del modelo, no cambiar un campo de autor.

Estado actual explícito: autorización letra Libre=declaración recibida; audio Libre, comparador, imágenes/referencias/fotos, biblioteca y otros ítems=not_requested (no se infiere permiso); asignaciones A/B/C/R=not_requested; anotaciones, cohorte evaluable y actas reales=blocked por admisión/asignación faltantes. Metrics reales=NULL. El contrato permite avanzar trabajo instrumental independiente; no presenta D13 materialmente cerrado.

Derechos se revalidan antes de encolar cada uso y antes de serving: letra→own/assistant/licensed/public_domain; audio/imagen→declaración exigible; foto real→self o consented, conforme D03. La evidencia distingue declaración, licencia específica, alcance y consentimiento de persona. Foto cuyo carácter real es desconocido queda bloqueada, no n_a. Faltante/revocado/discrepancia de propietario da rechazo sanitizado antes job/engine/transferencia. Pruebas E2E-04 quitan cada declaración y cada consentimiento por separado, prueban cero jobs/efectos y logs/capturas sin contenido privado; fixtures se rotulan synthetic.

## 4. Schemas externos cerrados, dominios y fallos

Esta notación es normativa y compilable a JSON Schema futuro: `{a:T,b:U}` enumera **todas** las claves obligatorias; `T?` significa valor T o NULL, nunca clave omitida. Todos los objetos `additionalProperties:false`, parsing UTF-8 sin BOM/duplicados; arrays ordenados sin duplicados donde tienen identidad; cero coerción, bool distinto de int, NaN/Inf rechazados. `U` ULID26, `S` SHA25664 lowercase, `N` entero0..2^63−1, `P` entero1..2^63−1, `F` binary64 finito, `B` bool, `UTC` ISO8601 UTC con Z; `L` ASCII1..128 [a-zA-Z0-9_.:-], `Text` Unicode0..32768. Tiempos son segundos F≥0 con stop>start y ≤duration; frames enteros; unidades explícitas, no ms persistidos. `[T]` lista0..100000; vacío sólo donde las reglas lo permiten. Cada payload≤65536bytes para ProfileRef; capturas más grandes usan ByteRef según D04, no eludir quota profile. `Ref` es **exactamente** CapturedRef D02/D04 y `Bytes` exactamente ByteRef D04, no una copia aproximada. `RightsSnapshotRef` es **exactamente** D05 `{family:rights,reader:production.rights,version:1,sha256:S}`, referencia al snapshot sellado D03; es distinto de CapturedRef y no amplía su enum family. No guardar paths locales en formatos públicos.

`Fact={state:known|unknown|not_applicable,value:F?,unit:s|ratio|lufs|dbtp|bytes|count|hz|score,proof_ref:Ref?}`: known exige value/proof noNULL; otros ambosNULL y reason externo en registro. `Metric={state:measured|indeterminate|not_applicable,value:MetricValue?,unit:s|ratio|score|rating|lufs|dbtp,count:N,reference_ref:Ref?,raw_ref:Bytes?,reason:NULL|NO_REFERENCE|NO_EVENTS|AMBIGUOUS|TOOL_FAILED|SOURCE_MISMATCH|INCOMPLETE|PRECISION_UNPROVEN}`: measured exige count>0,value finito,reference/raw noNULL,reasonNULL; indeterminate valueNULL/reason noNULL; not_applicable valueNULL,count0,reasonNO_EVENTS y prueba referida. Ratio/score0..1; rating humano entero1..5 (no bool ni float integral coercionado); métricas temporales≥0; LUFS/dBTP pueden ser negativas. No count0→1 ni resultado ausente→0 de error. MetricValue se discrimina por unit: rating es entero JSON N acotado1..5; las demás unidades conservan F finito y sus límites originales; rating exige entero JSON1..5 cuando measured; indeterminate/not_applicable conservan valueNULL y todas sus reglas anteriores. Fact no recibe unit rating: conserva score normalizado y su dominio original. No convertir rating a ratio/score ni usar count para representarlo; la puntuación de Observation sigue entero1..5.

| Reader / family | Payload exacto y reglas |
|---|---|
| `production.cohort_rubric/1` / profile | `{schema_version:1,rubric_id:U,option:CM-O1|CM-O2|CM-O3,status:proposed|ratified,root_ratification_ref:Ref?,metric_rules:[{method:beats|key|sections|lyrics_timing|loudness|render|quality|f19|artwork|recovery,name:L,comparison:le|ge|eq,value:F,unit:s|ratio|score|rating|lufs|dbtp|count,policy_ref:Ref}],human_rules:[{method:karaoke|artwork_generate|artwork_reference|full_render|f19|paired_quality|backup_recovery,dimensions:[L],minimum_score:4,max_major:0,max_critical:0}],cohort_policy:{music_min_items:8,omission_min_items:2,repetition_min_items:2,silence_min_items:2,long_min_items:2,whole_duration_required:true,libre_415_required:true},performance_option:CM-P1|CM-P2|CM-P3,performance_policy_ref:Ref,resource_policy_ref:Ref,paired_policy_ref:Ref}`; metric_rules exactamente reglas numéricas §5/6 de opción elegida, sin repetir/missing ni fields arbitrarios; dimensiones exactamente §6, policy_ref congela métodos/units/nullability de cada regla; rating en metric_rules exige value entero4 para los cinco mínimos humanos; restantes value:F/units originales intactos; ratified requiere autoridad ROOT real |
| `production.cohort_freeze/1` / profile | `{schema_version:1,freeze_id:U,created_at:UTC,contract_ref:Ref,rubric_ref:Ref,cohort_ref:Ref,assignment_refs:[Ref],annotation_refs:[Ref],method_profile_refs:[Ref],status:proposed|ratified,root_ratification_ref:Ref?}`; ratified necesita recibo ROOT real y todos prerequisitos del alcance declarado. proposed no libera método. No autorreferencia SHA del propio archivo |
| `production.cohort/1` / catalog | `{schema_version:1,cohort_id:U,revision:P,parent_ref:Ref?,created_at:UTC,scope:music|artwork|full_render|backup_recovery,status:planned|admitted|blocked,items:[Item],missing_requirements:[L],rubric_ref:Ref}`; admitted exige cupos/material/derechos reales completos y missing=[]; planned/blocked no aceptan producto |
| `Item` interno cohorte | `{item_id:U,source_ref:Ref?,audio_binding_ref:Ref?,lyrics_context_ref:Ref?,rights_refs:[RightsSnapshotRef],duration_s:F?,frames:P?,sample_rate:P?,language:es|not_applicable,tags:[omission|repetition|silence|instrumental|long|libre_415|dense|sparse|tempo_change|key_change],status:not_requested|blocked|admitted,reason:NULL|RIGHTS_MISSING|SOURCE_MISSING|CONSENT_MISSING|ASSIGNMENT_MISSING|REFERENCE_MISSING}`; admitted audio exige bindings/rights/N/Fs/duration exactos y reasonNULL; pendiente no inventa hashes/tiempos; artwork/library no audio→N/Fs/durationNULL sin audio ficticio |
| `production.human_assignment/1` / binding | `{schema_version:1,assignment_id:U,person_id:U,role:annotator_a|annotator_b|adjudicator|reviewer,item_ids:[U],independent_from_model:B,blind_to_outputs:B,conflict:none|declared,status:not_requested|accepted|declined,accepted_at:UTC?,acceptance_ref:Ref?}`; accepted requiere dos noNULL, flags true para A/B/C, conflictos declarados bloquean árbitro propio; no firma fabricada |
| `production.annotation/1` / measurement | `{schema_version:1,annotation_id:U,item_id:U,assignment_ref:Ref,source_ref:Ref,audio_binding_ref:Ref,lyrics_context_ref:Ref?,created_at:UTC,complete:B,coverage_start_s:F,coverage_stop_s:F,words:[Word],regions:[Region],beats:[Beat],keys:[KeySpan],sections:[Section],uncertainties:[Uncertainty],method_ref:Ref}`; complete true sólo cobertura0..N/Fs y categorías completas; archivo congelado antes output-model reveal |
| `Word` | `{occurrence_id:U,lyrics_ordinal:N?,binding_id:U?,token_id:U?,char_start:N?,char_stop:N?,occurrence_index:N,text_ref:Ref,start_s:F?,end_s:F?,state:sung|omitted|unmatched|uncertain,confidence:F?}`; referencia token/slices/binding reales, no copiar letra pública. sung/uncertain intervalos noNULL; omitted ambosNULL/token noNULL; unmatched intervalos noNULL/token/slicesNULL. confidence NULL o0..1; jamás1 por omisión. Letras repetidas tienen occurrence_id distintos y ocurrencia creciente; omisión no aparece como palabra cantada |
| `Region` / `Beat` | Region=`{region_id:U,kind:acoustic_silence|instrumental|uncertain,start_s:F,end_s:F,proof_ref:Ref}`. Silencio acústico no equivale a ausencia de voz; instrumental puede sonar. Beat=`{beat_id:U,time_s:F,metrical_index:N?,state:confident|uncertain,confidence:F?}`; time<duration, strictly increasing, índiceNULL si no se demuestra |
| `KeySpan` / `Section` / `Uncertainty` | KeySpan=`{span_id:U,start_s:F,end_s:F,tonic:N?,mode:major|minor|other|unknown,state:confident|uncertain}`; tonic0..11 si major/minor, restoNULL; modulación se anota por span sin forzar key global. Section=`{section_id:U,start_s:F,end_s:F,label:verse|chorus|bridge|intro|outro|instrumental|other|unknown,state:confident|uncertain}`; partición completa0..duration sin gap/overlap, etiqueta por escucha, no tags. Uncertainty=`{uncertainty_id:U,category:word|beat|key|section|region,member_id:U,start_s:F?,end_s:F?,reason:inaudible|polyphonic|boundary|tonal_ambiguous|disagreement,adjudication_ref:Ref?}`; member existe, NULL temporal sólo word omitted |
| `production.annotation_consensus/1` / measurement | `{schema_version:1,consensus_id:U,item_id:U,a_ref:Ref,b_ref:Ref,adjudicator_ref:Ref?,frozen_at:UTC,agreed_annotation_ref:Ref?,disagreements:[{category:L,a_id:U?,b_id:U?,resolution:agreed|unresolved,proof_ref:Ref?}],status:complete|indeterminate}`; indeterminate no adjudicación/resultados fabricados; todos desacuerdos preservados y decididos antes outputs; árbitro obligatorio donde hay resolución |
| `production.analysis_method_profile/1` / profile | `{schema_version:1,method:beats|key|sections,profile_id:L,analyzer_ref:Ref,decoder_ref:Ref,rubric_ref:Ref,parameters:Parameters}`; beats Parameters=`{tolerance_s:0.070,f1_min:0.90,matching:ordered_max_cardinality_min_error_v1,confidence_policy:report_all_v1}`; key=`{accuracy_min:0.90,scoring:exact_tonic_mode_duration_v1,unknown_policy:block_acceptance_v1}`; sections=`{boundary_tolerance_s:1.0,boundary_f1_min:0.85,label_accuracy_min:0.85,matching:ordered_max_cardinality_min_error_v1,textual_is_measurement:false}`. Literales CM-O1 sólo tras ratificar; alternativas usan otro perfil/SHA |
| `production.alignment_profile/1` / profile | `{schema_version:1,profile_id:alignment_es_v1,aligner_ref:Ref,decoder_ref:Ref,rubric_ref:Ref,parameters:{median_max_s:0.100,p95_max_s:0.250,recall_min:0.95,precision_min:0.95,omission_accuracy_min:0.95,repetition_recall_min:0.95,silence_false_positive_max:0,quantile:nearest_rank_v1,normalization:nfc_casefold_compare_only_v1,matching:ordered_occurrence_v1,chunking:full_global_offsets_v1},correction:{allowed_fields:[state,start_s,end_s,confidence],preserve_tokens:true,preserve_audio:true,preserve_text:true},export:{lrc_rounding:nearest_ties_even_centisecond_v1,srt_rounding:nearest_ties_even_millisecond_v1,missing_policy:omit_with_sidecar_v1,uncertain_policy:explicit_opt_in_v1}}`; no capacidades por pin solo |
| `production.analysis_method/1` / measurement | `{schema_version:1,method:beats|key|sections,state:measured|indeterminate,profile_ref:Ref,audio_binding_ref:Ref,execution_ref:Ref,data:MethodData,confidence:F?,warnings:[L]}`; beats data=`{events:[Beat]}`; key=`{spans:[KeySpan]}`; sections=`{segments:[Section],origin:measured|textual}`. Measured exige datos íntegros y medición real; textual no pasa criterio medido, warnings no ocultos |
| `production.alignment/1` / measurement | `{schema_version:1,state:measured|indeterminate,profile_ref:Ref,audio_binding_ref:Ref,lyrics_context_ref:Ref,execution_ref:Ref,timing_revision_ref:Ref?,coverage_start_s:F,coverage_stop_s:F,words:[Word],regions:[Region],unmatched:[Word],chunk_receipts:[Ref],warnings:[L]}`; root de timing y token IDs D03 preservados; unmatched sólo observación externa, no nueva fila token en m3_timing_word. Repetición extra no se añade al texto histórico. Si no cabe sin conservar tokens, nueva alineación inicial o evidencia unmatched separada, nunca corrección que cambie letra |
| `production.cohort_metrics/1` / measurement | `{schema_version:1,run_id:U,item_id:U,method:beats|key|sections|lyrics_timing|loudness|render|quality|f19|artwork|recovery,freeze_ref:Ref,reference_ref:Ref?,result_ref:Ref?,metrics:[{name:L,metric:Metric}],counts:[{name:L,value:N}],verdict:pass|fail|indeterminate,reason_codes:[L],human_review_refs:[Ref],raw_refs:[Bytes]}`; nombres exactos por método §5/6 y unidades obligatorias del párrafo siguiente, sin dict libre, faltar métrica/count esperado da indeterminate. pass exige todos gates de su método, ninguna referencia faltante |
| `production.human_review/1` / measurement | `{schema_version:1,review_id:U,assignment_ref:Ref,item_ids:[U],method:karaoke|artwork_generate|artwork_reference|full_render|f19|paired_quality|backup_recovery,freeze_ref:Ref,result_refs:[Ref],started_at:UTC,finished_at:UTC,complete:B,playback_ref:Ref?,observations:[{dimension:L,state:scored|not_applicable,score:N?,defect:none|minor|major|critical,position_s:F?,note_ref:Ref?}],verdict:pass|fail|indeterminate,signed_at:UTC?,signature_ref:Ref?}`; firma/resultado completo para pass, score1..5 sólo dimensiones rúbrica; defectos conservados; ausentes dan indeterminate, no acta asistente inventada |

Los cinco agregados humanos cerrados `render_human_min_score`, `quality_human_min_score`, `f19_human_min_score`, `artwork_human_min_score`, `recovery_human_min_score` usan exclusivamente Metric.unit=rating: mínimo entero de todas las Observation.state=scored requeridas del método/ítem/run o pareja, sin promedio ni selección favorable. Count es número real de observaciones puntuadas (no el rating); reference_ref resuelve rúbrica/actas independientes y raw_ref sus bytes privados con custodia. Cada dimensión aplicable debe estar presente y puntuada; una requerida ausente o no puntuada da indeterminate/valueNULL, no mínimo sobre subconjunto. Dimensiones legítimamente not_applicable sólo según §6 permanecen explícitas con prueba y no reciben score5. Si no hay observaciones puntuadas, indeterminate/NO_EVENTS/count0; no invocar N/A para eludir un gate humano requerido. Un rating measured4 pasa el límite4, rating3 falla; score4, rating0/6/4.0/true y count4 sin observaciones son inválidos. Todos los mínimos humanos siguen4 en human_rules y metric_rules con unit=rating y comparison=ge/value4, sujetos a ratificación ROOT. Los otros nombres conservan unidades: métricas de errores/tiempos/diferencia LU usan s o lufs según §5/6, las de true peak dbtp, precisión/recall/F1/accuracy/preference/byte_identity ratio0..1 y scores normalizados score0..1 si un perfil los solicita; los recuentos permanecen counts:N. No se cambia fórmula, dominio, nullability o umbral de ninguna métrica existente.

Refs con ownership/hash/version/audio distinto, annotations incompletas, herramienta fallida, EOF ausente, método fuera de dominio, confianza no calibrada o cobertura temporal insuficiente bloquean aceptación. Confianza del modelo se registra NULL si no se conoce; bins[0,.5),[.5,.8),[.8,1] y NULL se reportan separados, además del resultado sobre **todos** los eventos. No descartar baja confianza ni anotaciones inciertas para mejorar cifras. Referencia no resoluble produce métrica indeterminate con recuento incierto explícito; aceptación del ítem bloqueada hasta adjudicación. Las categorías esperadas y ausencias permanecen en informe, sin ceros ficticios.

Los readers de bytes de soporte nuevos quedan cerrados por tipo: `production.cohort_raw.annotation/1`, `.playback/1`, `.telemetry/1`, `.human_note/1`, `.screen_capture/1`, `.stdout/1`, `.stderr/1`, family measurement, payload **bytes originales íntegros**, no JSON libre ejecutable. Parser/format/platform/schema del registro productor quedan en Ref de perfil/ejecución; unknown/type mismatch rechaza. Captura pantalla es formato admitido/pinado D07, no nombre que permite cualquier decoder; audio PCM/stdout de D05 conserva sus readers propios. Conjunto mínimo de raw para pass incluye fuente, medición/runner, anotación y acta pertinentes con custody/ownership reales.

## 5. Métodos numéricos y rúbrica CM-O1 propuesta antes de pruebas

Cada canción/método se evalúa completa e individualmente; bins/estratos son diagnósticos adicionales. Numerador y denominador enteros se conservan. Comparaciones sin redondear ni tolerancia flotante adicional; ratio se decide por productos enteros, tiempos desde referencias sin redondear. Percentil nearest-rank: ordenar e1≤…≤en; mediana=eceil(.5n), P95=eceil(.95n), n>0. Nunca media de medianas ni de porcentajes. n=0 es indeterminate/NO_EVENTS; métricas específicas sin fenómeno real son not_applicable con prueba y no rellenan los cupos de cohorte.

**Palabras.** Referencia humana usa ocurrencias cantadas, tokens históricos estables y offsets globales. NFC+casefold sólo sirve para comparación; los slices/textos históricos se conservan exactamente. Puntuación no es token cantado; límites Unicode/separación de apóstrofos y guiones se fijan por versión tokenizador referida antes anotar; si el tokenizador cambia, nueva alineación raíz. Emparejar secuencias por token/context/binding y ordinal de ocurrencia, maximizar número de pares válidos monótonos y luego minimizar suma de diferencias absolutas de onsets; desempate lexicográfico de IDs. No nearest independiente que reutilice una palabra ni alineación retrospectiva que esconda repetición. La identidad de ocurrencia se adjudica sin mirar timestamps del modelo.

Para cada par, onset_error=abs(pred.start−ref.start), offset_error=abs(pred.end−ref.end). Guardar ambas distribuciones; gate **cada una** mediana≤0,100s y P95≤0,250s. TP pares; FN ocurrencias cantadas no predichas; FP predicciones sin ocurrencia real. Recall=TP/(TP+FN) y precision=TP/(TP+FP), ambas≥0,95. Omisiones: exactitud=omisiones marcadas missing / omisiones reales, ≥0,95, más falsos missing cuentan FN. Repeticiones: recall de ocurrencias repetidas reales≥0,95 y extras inexistentes cuentan FP; dos timestamps de una ocurrencia no prueban repetición. `unmatched_ref`, `unmatched_pred`, `omitted_ref`, `false_missing`, `repeat_ref`, `repeat_matched`, `uncertain_ref` cuentan separados. Tiempos missing son NULL, nunca0 o interpolados.

En intervalos acoustic_silence/instrumental sin voz anotada, ningún highlight de palabra inexistente: silence_false_positive_count=0. Se guarda duración de intersección de cada predicción con regiones y catálogo de incidencias; no confundir silencio vocal con acústico. Una palabra legítima junto a frontera no falla sólo por intersección parcial; manda ocurrencia real/ausente y su error temporal. Chunking permite fragmentos sólo con spans/offsets globales, overlaps y EOF acreditados; deduplicar por identidad demostrada, conservar problemas de frontera. Libre completo tiene anotación y resultado desde0 hasta duración efectiva, incluyendo último fragmento y silencios; 180s es frontera de caso adverso, no límite de canción.

Names/counts cerrados lyrics_timing: metrics onset_median,onset_p95,offset_median,offset_p95,precision,recall,omission_accuracy,repetition_recall; counts tp,fp,fn,unmatched_ref,unmatched_pred,omitted_ref,omitted_correct,false_missing,repeat_ref,repeat_matched,uncertain_ref,silence_false_positive_count,total_reference_words,total_predicted_words. Lo no aplicable mantiene entrada tipada, no desaparece.

**Beats.** Anotación auditiva independiente y adjudicación de pulso/medida; eventos de modelo ni grilla BPM no son ground truth. Matching uno a uno monótono dentro |Δt|≤0,070s, maximiza TP, minimiza error absoluto, desempata IDs. FN/FP incluyen todos eventos no emparejados; F1=2TP/(2TP+FP+FN)≥0,90 **por canción**, igualdad permitida. Half/double tempo no se perdonan con métrica alternativa; se informan artefactos. No cortar intro/outro o ajustar offset después. Metrics beat_precision,beat_recall,beat_f1,beat_error_median,beat_error_p95; counts tp,fp,fn,uncertain_reference_beats,total_reference_beats,total_predicted_beats. P95 diagnóstico, no límite nuevo secreto. Referencia ambigua/sin pulso determinable es indeterminate, no F1=1.

**Key.** Referencia combina escucha independiente y, si se usa, prueba de instrumentación musical sin outputs evaluados; no anotación basada en estimator competidor ni tags del prompt. Spans cubren tiempo completo, incluidos cambios; tonic0=C,…11=B y major/minor exactos; relativo/equivalente enarmónico se normaliza a pitch class sin perdonar modo equivocado. Accuracy=sum duración donde tonic y mode exactos / duración con referencia tonal determinada; ≥0,90. Unknown/other/reference ambiguo se cuenta en duración total e impide acceptance del ítem (no excluir para aprobar); no se exige inventar tonalidad en silencio. En spans instrumental tonal se evalúa; en silencio referencia unknown tipada no inventa key. Metrics key_exact_duration_accuracy; counts reference_tonal_frames,correct_tonal_frames,unknown_reference_frames,total_frames (spans se convierten a frames nearest-ties-even una vez, con recibo). La política de aceptación `unknown_policy:block_acceptance_v1` se aplica a key cuando hay ambigüedad tonal, no penaliza silencios acústicos identificados: se conservan como not_applicable con prueba, denominador y duración se publican. No redefine whole duration de otros métodos.

**Sections.** Escucha independiente delimita partición completa y etiquetas cerradas; etiquetas de letra no prueban boundaries. No incluir endpoints0/duration como TP gratis: evaluar sólo fronteras interiores. Matching ordenado±1,0s, F1≥0,85. Etiqueta: duración de intersecciones con label correcto / duración total evaluable; ≥0,85. Introducciones/outros/instrumentales se conservan. Unknown/uncertain reference bloquea acceptance; una sola sección legítima no tiene fronteras→boundary_f1 not_applicable probado, exige exactitud etiqueta y revisión humana, no F1=1. Metrics boundary_precision,boundary_recall,boundary_f1,section_label_duration_accuracy; counts boundary_tp,boundary_fp,boundary_fn,correct_label_frames,total_frames,uncertain_reference_frames. Límites frame definidos como key, sin gap/overlap al cuantizar.

**Loudness.** M-17 compara resultado real con medición D05 independiente pin/calibración/EOF por plataforma; objetivos finales streaming−14±0,5LU, broadcast−23±0,2LU, podcast−16±0,5LU y TP≤−1dBTP se toman de D05, con intervalos conservadores completos, no se inventa tolerancia adicional. Comparación de dos medidores: diferencias y cotas acreditadas; concordancia si intervalos se intersectan, disjuntos fail, falta precisión indeterminate. Esto no certifica pin ni norma. Metrics input_loudness_difference,input_true_peak_difference,final_integrated_loudness,final_true_peak; counts decoded_frames,channels. Original-byte export no requiere estas mediciones y conserva su excepción D05.

**LRC/SRT y corrección.** Corrección conserva IDs/context/bindings/audio/texto/initial_result D03; nuevo hijo, nunca edit in-place. LRC nearest-ties-even centésimas, SRT milésimas, valores desde tiempos globales íntegros y carry correcto. Colisión de redondeo no se resuelve desplazando palabra: agrupar líneas simultáneas cuando perfil lo permite, o rechazar incompatibilidad y ofrecer formato con precisión suficiente. LRC conserva comienzo de línea; SRT intervalo válido y orden, sin end≤start; no afirma precisión de palabra que formato no representa. Missing se omite del contenido timed y se conserva en sidecar de estado con token IDs; incertidumbre requiere opt-in y marca sidecar/UX, sin palabras cantadas ficticias. Sidecar privado usa ByteRef/reader nuevo futuro `production.timing_export_status/1` con exactamente `{schema_version:1,timing_revision_ref:Ref,format:lrc|srt,omitted_token_ids:[U],uncertain_token_ids:[U],quantization_profile_ref:Ref}`; ninguna propiedad nueva en export D04.

## 6. Experiencia humana, recursos, comparación y recovery

Scores comunes1=impide uso,2=defectos frecuentes,3=utilizable con defectos,4=útil con defectos menores,5=útil sin defectos observados; no promedio sustituye dimensiones. Pass humano exige complete/firma reales, cada dimensión requerida≥4 y cero major/critical. Minor se conserva. Dimensiones por acta: karaoke `synchrony,word_identity,readability,usefulness`; artwork_generate/reference `readability,composition,reference_fidelity` (reference_fidelity not_applicable sólo generate); full_render `readability,synchrony,continuity,audio_integrity`; f19 `motif_recognition,structure_recognition,accompaniment_usefulness,artifact_severity`; paired_quality `musicality,intelligibility,artifacts,style_adherence,naturalness,instrumentation,accent,major_cue,crescendo_cue,clean_vocals_cue,outro_cue`; recovery `query_correctness,search_correctness,playback_integrity`. `artifact_severity` score5=sin defecto y1=grave. Se observa principio/fin completo, pausas y seeks relevantes con recibo. Revisión humana no reemplaza medición temporal/byte checks.

Los tags interpretativos de **LETRA**, incluidos voz/naturalidad/acento/instrumentos/major/crescendo/clean vocals/outro, son input efectivo preservado; se evalúa fidelidad al prompt por escucha humana con rúbrica separada, nunca se usan como ground truth de sección, palabra cantada, tonalidad o confidence. Cada cue solicitado tiene observación de intervalo real y nota; no solicitado queda not_applicable explícito en acta, sin score5 por ausencia. Observation usa su forma cerrada de §4; state=scored exige score1..5; not_applicable scoreNULL y nota de ausencia de cue solicitada, conserva la dimensión. Prompt major sin tonalidad medida no prueba major: `major_cue` es juicio de fidelidad y key metric tiene referencia independiente. Naturalness/instrumentation/accent se revisan siempre; ausencia de intención explícita se juzga por utilidad y defectos audibles, no confianza del modelo. Ni confianza automática ni etiqueta reemplaza la escucha.

**N0 minutos propuestos, pendiente D07/ROOT.** CM-O1 propone 1080p16:9 y1080×1920,30/1fps, cada canción completa y perfil propio, CPU offline sin requerir modelo16GB. Tiempo wall comienza job aceptado sin cola ajena, incluye lectura/features/captura/encode/medición/publicación y termina recibo durable; queue wait, setup frío y warm time se registran aparte, no se ocultan. Tres runs completos por perfil, uno frío y dos warm; **cada** run≤max(600s,4×duración efectiva), y Libre nominal255s→1020s (17min) por perfil, nunca clip. Alternativas antes medir: CM-P2≤6×duración con floor600s (25,5min Libre); CM-P3≤2× con floor300s (8,5min). No performance resultado real aquí; perfiles finales/font/codec/browser quedan D07, no seleccionados por prosa D06. N0 no añade otro modelo residente; renderer/FFmpeg CPU se separa de música GPU.

Proposal sync/export: tiempo final de vídeo frente N/Fs error≤1/30s; palabra/pantalla≤1cuadro a30fps, deriva A/V principio/interior/fin≤1cuadro, sin ocultar error de alineación: renderer se mide contra timing_revision, karaoke real además contra humanos. Decodificar final hasta EOF/fps/resolución/audio LUFS/TP y reproducir entero en navegador y reproductor independiente ya licenciado; pins/codec/fonts permitidos D07 antes RED. No instalación nueva en esta pasada. Capturas cortadas/ilegibles, EOF parcial, drift o decode fallido impiden pass.

Reader futuro `production.temporal_cue_evidence/1`, family measurement, exactamente `{schema_version:1,run_id:U,audio_binding_ref:Ref,timing_revision_ref:Ref,timeline_ref:Ref,render_ref:Ref,decoder_ref:Ref,frame_count:P,fps_num:30,fps_den:1,decoded_duration_s:F,complete:B,cues:[{token_id:U,reference_start_s:F,reference_end_s:F,first_highlight_frame:N,last_highlight_frame:N,observed_audio_start_s:F?,observed_audio_end_s:F?,screen_capture_ref:Bytes,audio_observation_ref:Ref?}],av_checkpoints:[{reference_time_s:F,audio_time_s:F,video_frame:N,measurement_ref:Ref}],playback_refs:[Ref]}`. Cues incluyen **todas** las palabras timed, no una muestra favorable; missing listado aparte por timing sidecar. Onset screen error=abs(first_frame/30−revision.start) y offset=abs((last_frame+1)/30−revision.end); observación real de canto contra annotation conserva su propio error, nunca mezcla dos referencias. Checkpoints principio, todos intervalos de10s y fin efectivo (último parcial incluido); deriva=abs(audio_time−video_frame/30), no sólo duration metadata. Datos sólo de cuadros/audio medidos, no inferidos de receta. Metrics render_duration_error,render_word_screen_max_error,render_av_max_drift,render_wall_time_s,render_human_min_score; counts decoded_audio_frames,decoded_video_frames,expected_timed_words,observed_timed_words,missing_cues,major_defects,critical_defects. Performance compara cada run con objetivo congelado y conserva frío/warm por separado.

**RTX5070 CUDA12GB.** Baseline propuesto libre comprobada con Ollama/modelo descargado sólo por intervención propia futura; tope propio=`free_vram_bytes−1610612736` (1,5GiB de margen) y free_vram_bytes>1610612736 antes iniciar; si tope≤0 blocked. Nunca fracción de12GB ni suponer capacidad por total. Un modelo propio BF16 y modo/tier4 explícitos; precisión/mode/offload efectivos en receipt. Sólo capacidades locales ganadoras M0 probadas, sin exigir pesos≥16GB. Telemetría CPU% por núcleo/total, RSS/process-tree y RAM/VRAM dedicada/compartida en bytes con timestamp monotónico≤1s (más alloc-picos oficiales), tiempos fases, temperatura opcional, crashes/oom/offload/spill. Shared GPU memory por encima baseline, residency ajena, sample gap>2s o descarga no acreditada bloquea evidencia de ausencia de spill; RAM no es prueba suficiente. Si plataforma no ofrece contador necesario, state indeterminate, no claim sin spill. CPU/RAM límite: RSS árbol≤min(17179869184bytes, RAM libre inicial−2147483648bytes), si presupuesto≤0 blocked; swap/offload sólo modo explícito aprobado, no fallback silencioso. Unload verifica fin árbol propio y regreso VRAM≤baseline+268435456bytes dentro30s, tres muestras1s; no parar servicio Ollama ni borrar modelos. Registrar estado previo y sólo restaurar modelo si esta ejecución lo descargó. Estos valores son opciones de proyecto pendientes, no especificación NVIDIA ni hechos ejecutados.

Readers policy nuevos, family profile, todos cerrados:

- `production.performance_policy/1`: `{schema_version:1,option:CM-P1|CM-P2|CM-P3,profiles:[{width:1920,height:1080}|{width:1080,height:1920}],fps_num:30,fps_den:1,cold_runs:1,warm_runs:2,minimum_wall_budget_s:F,duration_multiplier:F,word_screen_max_frames:1,av_drift_max_frames:1,checkpoint_step_s:10,include_publish:true,include_measurement:true}`. P1=600/4, P2=600/6, P3=300/2, no mezcla libre de límites; profile exact D07 y whole audio obligatorio.
- `production.resource_policy/1`: `{schema_version:1,gpu_class:rtx_5070_12gb,precision:bf16,resident_model_max:1,vram_margin_bytes:1610612736,ram_margin_bytes:2147483648,rss_ceiling_bytes:17179869184,sample_period_s:1,max_sample_gap_s:2,unload_budget_s:30,unload_delta_bytes:268435456,unload_samples:3,shared_spill_allowed:false,offload_policy:explicit_mode_only,restore_ollama:only_own_unload}`; mode/tier efectivos y capacidad comprobada se referencian D10/D11, no nombre modelo inventado.
- `production.paired_policy/1`: `{schema_version:1,min_complete_pairs:8,reviewers_per_pair:3,min_high_preferences:2,required_equal_fields:[text,language,style,negative_prompt,duration,lyric_performance_tags,reference,metadata,tokenization,seed_when_supported],quality_delta_ref:Ref,listen_target_lufs:-23,level_difference_max_lu:0.2,limiter:false,blind:true,select_favorable_samples:false}`; delta schema D10 previo, target menor excepcional se captura antes escucha con razón TP y misma medición conservadora.

Reader de ejecución observada `production.resource_measurement/1`, family measurement, exactamente `{schema_version:1,run_id:U,execution_ref:Ref,resource_policy_ref:Ref,performance_policy_ref:Ref?,platform_ref:Ref,model_pin_refs:[Ref],effective_mode_ref:Ref,cuda_ref:Ref?,started_at:UTC,finished_at:UTC,wall_time_s:F,queue_wait_s:F,cold:B,duration_s:F,before_ref:Ref,after_ref:Ref,telemetry_ref:Bytes,samples:[{time_s:F,cpu_total_percent:F?,cpu_core_percent:[F],rss_tree_bytes:N?,ram_free_bytes:N?,vram_dedicated_bytes:N?,vram_shared_bytes:N?,resident_models:N?,state:observed|unavailable,reason:NULL|COUNTER_UNAVAILABLE|SAMPLE_GAP|SOURCE_MISMATCH}],official_peak_refs:[Ref],unload_ref:Ref?,ollama_intervention_ref:Ref?,verdict:pass|fail|indeterminate}`. %0..100 según métrica núcleo/total normalizada capturada, no agregado>100 ambiguo; tree RSS y model/count/VRAM contienen sólo medición propia identificada por receipt privado sin PID público. Time monotónico de0..wall_time, incluye fin, sin gap oculto; unavailable NULLs y reason real. CUDA_refNULL para N0CPU, no ejecución CUDA ficticia. Before/after readers usan exactamente el mismo schema de muestras con inventario proceso/modelos y prueba del dueño en receipt; registros propios identifican unload, restauración y comprobación. Unavailable cualquier contador necesario→indeterminate, OOM/spill/residency doble→fail; tiempo sólopropuesto no measurement. No se suman picos de etapas distintas como si fueran simultáneos.

**CA33 emparejamiento.** `production.paired_quality/1`, family measurement, exactamente `{schema_version:1,pair_id:U,item_id:U,freeze_ref:Ref,baseline_request_ref:Ref,high_request_ref:Ref,baseline_effective_ref:Ref,high_effective_ref:Ref,baseline_receipt_ref:Ref,high_receipt_ref:Ref,baseline_audio_ref:Ref,high_audio_ref:Ref,level_match_ref:Ref,resource_refs:[Ref],blind_order_ref:Ref,review_refs:[Ref],verdict:pass|fail|indeterminate}`. Mismo texto, idioma, estilo/negativeprompt, duration, seed por pareja cuando soportada, referencia y **tags de interpretación vocal de letra**, estructura, metadata efectiva y tokenización; pins/repos/weights/model/task/prompts reales capturados, no sólo texto UI. Única diferencia permitida: conjunto explícito de paramètres quality ratificado D10 antes generación (steps/mode/precision/etc); todas diferencias publicadas y no se induce claim por steps/XL/hash. Si modo cambia también prompt efectivo, pareja inválida para este criterio hasta control equivalente explícito; seed no soportada=NULL sin inventarla. Ambas ejecuciones mismas clases de recursos/licencias e igualdad de condiciones; varios seeds precongelados conservados, no selección favorable.

El recibo input efectivo sigue D02 sin añadir propiedades; la captura comparativa `production.paired_effective_input/1`, family measurement, exactamente `{schema_version:1,request_ref:Ref,lyrics_context_ref:Ref,prompt_bytes_ref:Bytes,lyric_performance_tags_ref:Bytes,metadata_ref:Ref,reference_refs:[Ref],seed:N?,seed_supported:B,model_pin_refs:[Ref],tool_pin_refs:[Ref],quality_parameters_ref:Ref,execution_receipt_ref:Ref}`. Texto/tags son bytes privados reales y comparados íntegros por SHA; seed_supportedfalse→seedNULL. Quality parameters es **schema cerrado ratificado del modo D10**, no JSON dict libre ni pin nuevo. Blind order reader `production.paired_blind_order/1` exactamente `{schema_version:1,pair_id:U,reviewer_id:U,order:baseline_high|high_baseline,randomization_receipt_ref:Ref,revealed_at:UTC?}`; sin reveal hasta acta sellada. Level match reader `production.paired_level_match/1` exactamente `{schema_version:1,pair_id:U,baseline_measurement_ref:Ref,high_measurement_ref:Ref,target_lufs:F,baseline_gain_linear:F,high_gain_linear:F,baseline_playback_ref:Ref,high_playback_ref:Ref,final_difference_lu:F,precision_refs:[Ref],limiter:false}`; gains finitas>0, diferenciaabs≤0,2 con cotas D05. Metrics quality_human_min_score,quality_level_difference_lu,quality_preference_ratio; counts pairs,reviewers,high_preferences,ties,baseline_preferences,major_defects,critical_defects. Preference ratio decide2/3 por par, no promedio cohorte.

Igualar reproducción por ganancia constante común a objetivo−23LUFS medido D05 y diferencia≤0,2LU con cotas acreditadas; sin limitador/compression, si TP impide−23 elegir nivel menor común **congelado antes escucha**, conservar receta/outputs originales. No normalizar archivos originales ni usar tags ReplayGain como medición. A/B ciego tres revisores propuestos, mínimo8pares completos; cada dimensión≥4, cero major/critical, al menos2/3prefieren alta por par y no degradación de dimensión frente baseline en ninguna revisión. Empates/no mejora→fail para claim mejora, no elimina utilidad base. Alternatives de muestra/listeners requieren perfil antes runs. Rights del comparador separados; comparación externa sólo uso autorizado específico y condiciones de prompt que pueda acreditarse; si metadata efectiva ajena desconocida, exploratory y nunca paired pass CA33.

**CA31 F19.** Upload/ruta de producto reales hasta child Take/linaje/rights y reproducción, no descriptor/native task solo. Motivo y estructura se anotan independentemente en fuente autorizada antes evaluar hijo; acta identifica intervalos reconocidos, acompañamiento útil y artefactos sobre canción íntegra. Misma rúbrica score≥4 cada dimensión, cero major/critical; limitations explícitos. No pitch/motif reconocimiento inventado por semejanza hash. Metrics f19_human_min_score; counts reviewed_dimensions,major_defects,critical_defects.

**CA25 artwork.** Generación Comfy headless Docker/CUDA y edición/ref son dos actas/runs; workflows/nodes/weights SHA seguros/revisados/licenciados y parámetros efectivos, múltiples opciones, tamaño/bytes/VRAM/RAM/tiempos/unload. Visual humano sobre resultado real, tipografía/legibilidad/crop y fidelidad ref donde solicitada; PNG mock no prueba. Metrics artwork_human_min_score; counts reviewed_options,major_defects,critical_defects. No checkpoint/workflow elegido aquí, D11 mantiene gate.

**CA43 biblioteca real.** Sólo copia autorizada, catálogo completo SHA/tamaño/IDs/path lógico before y after de originales intactos (incluido DB snapshot nativo y medios, no VHDX vivo). D09 exclusividad/backup restorable verificables antes activar; restore a biblioteca nueva dentro ext4 propio, raíz/UUID comprobados. Integridad SQLite/FK/FTS, queries/búsqueda/reproducción de todos medios de cohorte, jobs/leases inertes; activación/rollback es categoría separada, no se prueba borrando origen. Prueba interrupciones conforme D09 cuando autorizado; no ejecutar aquí. Metrics recovery_byte_identity_ratio (exactamente1),recovery_human_min_score; counts original_files,restored_files,missing_files,changed_original_files,query_failures,search_failures,playback_failures; todos fallos0 y originales íntegros. Synthetic backup rotulado no cierra CA43.

## 7. Evidencia separada y matriz de aceptación

`production.evidence_matrix/1`, family measurement, exactamente `{schema_version:1,matrix_id:U,contract_ref:Ref,freeze_ref:Ref?,entries:[Entry],actual_usage:null}`; Entry=`{criterion:CA04|CA17|CA21|CA25|CA28|CA29|CA31|CA33|CA43|CA49,scenario:E2E04|M17|M21|M25|M28|M29|M31|M33|M43|M49,category:documentary|cpu_fixture|synthetic_e2e|docker_ffmpeg_persistent|gpu_real|browser_player|human_review|music|full_render|backup_recovery|activation_rollback,status:not_requested|blocked|fail|pass,evidence_refs:[Ref],reason:L?}`. pass exige evidencia real de categoría, hashes/entorno/recibos íntegros; blocked/not_requested refs pueden estar vacíos, reason obligatorio. Todas categorías requeridas permanecen, no colapsar en pass global. No genera indicador de conformidad musical desde porcentaje cobertura ni fixture. Human actas y audio completo se conservan privados; informe público sanitizado.

| Criterio / escenario | Evidencia necesaria; frontera que sigue pendiente |
|---|---|
| CA04/E2E04 | Rights/consent por fuente, rechazo previo cola cero efectos y privacy; sintético separado de material admitido |
| CA17/M17 | Ground truth beats/key/sections independiente completo + loudness D05, por método/canción/confianza; textual no medido |
| CA21/M21 | Canto real castellano con omisiones/repeticiones/silencios, métricas §5 y acta utilidad; LRC/parser mock sólo CPU |
| CA25/M25 | Dos gates generación/edit referencia Comfy real GPU Docker + pins/telemetría/unload y acta visual |
| CA28/M28 | Full render/audio final EOF/fps/size/LUFS/TP/sync/word-screen, navegador y lector independiente íntegros + acta |
| CA29/M29 | Cada canción completa/perfil y3runs, objetivo previo/resource receipts RTX5070; clip no acredita minutos |
| CA31/M31 | F19 end-to-end real con input autorizado/linaje y motivo/estructura/acompañamiento anotados + acta |
| CA33/M33 | Pares effective text/tags/metadata/modes/pins/resources, niveles igualados, ciego y mejora/compromisos reales |
| CA43/M43 | Biblioteca real copia autorizada, guardas before/after, restore nuevo query/search/playback; activation separada |
| CA49/M49 | Matriz completa por evidencia/entorno/SHA, M2/hitos/gates heredados según ledger; ninguna prosa helper sustituye producto |

Esta entrega sólo categoría documentary. Música real, render completo y backup recovery tienen estados propios blocked; GPU/browser/human not_requested o blocked según prerrequisito, jamás pass. Numeradores y annotations reales NULL hasta adquisición. Actual IA tokens/tiempo/coste NULL: no escribe aggregate usage-meter ni usa estimaciones como consumo.

## 8. Contrato estricto del instrumento futuro de cobertura

El ledger §Cobertura estricta de fase es la autoridad del CLI/exits; este apartado concreta sus formatos. Código de `scripts/m3_coverage_gate.py` es producción y se mide whole; no excepción por llamarse helper. Scripts/test nuevos sólo después revisión contractual y RED causal. Dependencias existentes gestionadas, sin instalación ni intérprete máquina. El runner helper ofrece diagnóstico; no autoridad por `detalle.ficheros` redondeado, averages ni self-reported counters.

### 8.1 Inventario ROOT completo, bytes y paths

`changed-inventory.json`, reader `m3.coverage_inventory/1`: exactamente `{schema_version:1,phase_id:U,created_at:UTC,base_root_ref:Root,candidate_root_ref:Root,source_freeze_ref:Artifact,policy:Policy,files:[File],changes:[Change]}`.

`Root={root_id:U,path:Path,tree_sha256:S,inventory_ref:Artifact}`; path resuelve árbol físico privado relativo al directorio del inventario de fase y dentro del namespace ROOT, nunca checkout compartido. inventario íntegro de árbol=`{schema_version:1,root_id:U,files:[{path:Path,sha256:S,bytes:N,kind:regular}]}` orden lexical por UTF-8 de path. Hash árbol SHA256 del JSON canónico D02 UTF-8 completo de este inventario; SHA archivo cubre bytes completos, no contenido normalizado. Inventariar todos archivos del candidato con mtime sólo diagnóstico, sin derivar cambios de Git/mtime. Nada de carpetas excluidas silenciosamente: ROOT fija árboles privados completos y enumera explícitamente ausencias/provisión de deps; estos árboles de fase no son checkout compartido ni node_modules reales usados para ejecutar. `source_freeze_ref` enlaza corte y clasificación; untracked/new se trata como added. Verificar ausencia de symlink/junction/reparse/hardlink externo en cada componente y containment real antes lectura.

`Path` relativo raíz, UTF-8 NFC, separador `/`, sin drive/absoluto/UNC/colon/NUL/control/.. /./double slash/empty/componente trailingdot/space, sin reserved devices. Casefold y NFC collision en Windows o crossplatform→ambiguity exit1; resolver no con sufijos ni búsqueda de basename. `Artifact={path:Path,sha256:S,bytes:N}` refiere namespace privado evidence fijado ROOT; stdout logs pueden incluir rutas privadas y se sanitizan antes publicación, nunca se copian medios públicos.

`Policy={line_min:80,branch_required:B,branch_min:N?,scope:whole_changed_current,rounding:none,exceptions:[Exception]}`; branch_required true→branch_min80, false→NULL; fase puede exigir ramas adicionales pero nunca bajar80 en línea/statements. `Exception={path:Path,classification:test|config|prose|deleted_production,reason:L,proof_ref:Artifact,root_approval_ref:Artifact}`; ningún production_current exception. Deletion guarda proof sin inventar coverage de archivo ausente; rename mide newpath y conserva oldpath.

ROOT receipt reader `m3.coverage_root_receipt/1` exactamente `{schema_version:1,phase_id:U,created_at:UTC,base_root_id:U,candidate_root_id:U,base_tree_sha256:S,candidate_tree_sha256:S,inventory_sha256:S,source_freeze_sha256:S,approved_classification_ref:Artifact,namespace:Path,runner_ids:[U],root_execution_ref:Artifact}`. Este recibo R se construye después de I/F y E0; I no contiene root_receipt_ref ni otro hash/referencia a R. Su Artifact se registra después en official-reports.json. Root receipt proviene del orquestador, no del código evaluado; hash/custodia verificados contra comando real y árboles nuevamente leídos. Source freeze reader `m3.coverage_source_freeze/1` exactamente `{schema_version:1,phase_id:U,created_at:UTC,contract_ref:Artifact,base_inventory_ref:Artifact,candidate_inventory_ref:Artifact,classification_ref:Artifact,runner_config_refs:[Artifact],tool_lock_refs:[Artifact],root_ratification_ref:Artifact}`; existe antes I/runner; root_ratification_ref es preautorización A de insumos, no recibo de salida. F no refiere I/R/E0, runner executions, receipts, reports, verdict ni hashes anticipados de esos outputs. La cadena completa y los schemas de autoridad/ejecución se fijan en §8.2.1. Evidence Artefacts se resuelven respecto directorio de changed-inventory.json (mismo namespace ROOT); report manifest no puede redirigir outside. Raw generated en namespace **fuera** de base/candidate trees para no alterar diff durante medición. Source manifests y SHA inventories se vuelven a comprobar después runner; cambio concurrente da exit1/SOURCE_MISMATCH. Hardlinks sólo admitidos si todos aliases/resolved targets declarados quedan bajo árbol propio, ninguno fuente ajena modificable; en duda rechazar.

`File={path:Path,base_sha256:S?,candidate_sha256:S?,base_bytes:N?,candidate_bytes:N?,stack:python|istanbul|none,package:Path?,classification:production|test|config|prose,runner_id:U?,exception_ref:Artifact?}`; paths todos cambios de unión, base/candidate ambosNULL imposible; hash/size NULL parejas sólo inexistente. Production vigente requiere stack concreto/package/runner y exceptionNULL. Tests/config/prosa requieren excepción explícita; detector independiente ROOT revisa que código ejecutable no se oculte por extension/nombre. Gate usa inventarios completos recomputados, no confía clasificación por cuenta propia.

`Change={kind:added|modified|deleted|renamed,old_path:Path?,new_path:Path?,old_sha256:S?,new_sha256:S?}`; added oldNULL/newreal, deleted inverso, modified old=new, renamed ambosdistintos con bytes/hashes observados. Cada diferencia byte a byte aparece exactamente una vez, rename conserva dos paths Files y no deduce autoridad sólo SHA idéntico. Fuentes no cambiadas están en fulltree y raw pero no requieren threshold de fase; no borrarlas del report con exclude. Cualquier file faltante/extra/difference stale produce no-verde. Missing production en **raw existente** exit1; invalid/missing inventario estructural exit1 (no información para autorizar). Ninguna media global valida un fichero70/100.

### 8.2 Registro oficial/receipt/provenance y configuración sin exclusiones

`official-reports.json`, reader `m3.coverage_reports/1`, exactamente `{schema_version:1,phase_id:U,inventory_sha256:S,source_freeze_sha256:S,root_receipt_ref:Artifact,runner_records:[Runner],combined_records:[Combined]}`.

`Runner={runner_id:U,stack:python|istanbul,package:Path,platform:L,tool:{name:coverage.py|jest|vitest,version:L,executable_ref:Artifact,lock_refs:[Artifact]},receipt_ref:Artifact,raw_report_ref:Artifact,summary_ref:Artifact?,config_refs:[Artifact],effective_config_ref:Artifact,source_manifest_ref:Artifact,source_maps:[Map],test_result_refs:[Artifact]}`. Python raw coverage.py JSON no summary requerido; JS Istanbul `coverage-final.json` y `coverage-summary.json` diagnóstico. Referencias son bytes oficiales obtenidos por herramienta fijada, no JSON fabricado para obtener pass. SOURCE SHA se empareja con cada archivo exacto y rawReceipt; repos/pin/env efectivos preservados.

Receipt reader `m3.coverage_runner_receipt/1` exactamente `{schema_version:1,runner_id:U,phase_id:U,argv:[Text],cwd:Path,environment:[{name:L,value:Text}],started_at:UTC,finished_at:UTC,exit_code:N,stdout_ref:Artifact,stderr_ref:Artifact,tool_ref:Artifact,config_sha256:S,inventory_sha256:S,source_manifest_sha256:S,report_sha256:S,root_execution_receipt_ref:Artifact}`; exit0 obligatorio, tiempos monotónicos reales, no secret en environment ni invented runner. Env relevante completa (PYTHONPATH/COVERAGE/pytest/Jest/Vitest/locale) con explicit omissions de secretos y hash de configuración privada; omitir var que reduce scope invalida recibo. Receipt demuestra asociación/ejecución, no calidad ni autenticidad por sí sola: ROOT verifica tool/argv/raw/config/fuentes, custodia y runner log real. Self-signed reports no sustituyen control independiente. root_execution_receipt_ref refiere E_runner o E_combine de §8.2.1, emitido después de sus outputs y antes de este receipt C; E nunca contiene C ni official-reports.json. report_sha256 es SHA de raw_report_ref completo, no del registro posterior P. source_manifest_sha256 es del manifest observado independiente: éste no contiene C/E/P ni ref a sí mismo. config_sha256 refiere effective_config_ref completo, ya terminado antes E/C. En Combined este schema se usa con runner_id=combined_id, fijado en runner_ids de R junto con IDs de entradas; argv/tool/inputs se verifican además contra E_combine y sólo admite combinación oficial.

Effective config reader `m3.coverage_effective_config/1` exactamente `{schema_version:1,runner_id:U,source_roots:[Path],branch:B,include_patterns:[Text],omit_patterns:[Text],exclude_lines:[Text],ignore_patterns:[Text],test_nodes:[Text],config_refs:[Artifact],raw_effective_ref:Artifact}`. source_roots cubre raíces completas producción del paquete, no líneas diff ni fichero seleccionado favorable. omit/exclude/ignore=[]; incluir filtros que dejan producción fuera rechaza. Pragmas `no cover`, Istanbul/V8 ignore y comentarios/líneas excluidas sobre producción medida se detectan con fuentes/config oficiales, no se acepta counter0 como ausencia de exclusión. Defaults coverage.py se vacían explícitamente según versión fijada si excluyen líneas producción; report `excluded_lines` debe ser vacío en cada archivo medido. Test-node elección congelada antes ejecución, no permite reducir producción medida. Contrato `coverage.py branch_required` usa arcos oficiales por archivo; Istanbul branches completos cuando requerido.

Source manifest exactamente `{schema_version:1,runner_id:U,files:[{path:Path,sha256:S,bytes:N,raw_key:Text}]}` con conjunto completo de fuentes producción medidas; cada raw_key corresponde única/exactamente source path candidato, normalización de root prefix declarada en receipt (no strip basename/suffix). Python raw meta.version/timestamp/branch_coverage y files[path].executed_lines/missing_lines/excluded_lines/summary; fijar lector por toolversion, unknown version→exit2 pendiente, formato reconocido inconsistente→exit1. Lines son ints≥1, unique/disjoint, num_statements=|executed∪missing|, covered_lines=|executed|, missing_lines=|missing|; excluded=[]; min por fichero se calcula con enteros. Branch counters num_branches/covered_branches/missing_branches y executed_branches/missing_branches consistente bajo perfil oficial; no crear arcos nuevos. `percent_covered` y summary promedio se conservan diagnósticos, nunca autoridad.

Istanbul raw files exactamente path/statementMap/fnMap/branchMap/s/f/b conforme formato fijado y contador nonnegative int, mismo conjunto IDs en mapas/counters; arrays branch length exacta para locations, source ranges válidos y source SHA. Whole statements numerator=count(s[id]>0),denominator=len(s); whole lines agrupar statement ranges por start.line con count max de statements **como Istanbul oficial**, no sumar porcentaje o inventar líneas end. Guardar ambas líneas y statements; ambas≥80 (evita statements sin cubrir ocultos por línea parcialmente cubierta). Branch numerator=count de entradas branch counter>0,denominator=count completo de entradas, mínimo80 si requerido. Functions diagnóstico. Source maps `Map={generated_ref:Artifact,original_ref:Artifact,map_ref:Artifact,mapper_ref:Artifact,raw_key:Text}` con mapping oficial y source content SHA exactos; fuente completa, múltiple source+aliases sin relación única→exit1. Mapa faltante requerido→exit2; existente corrupto/incompleto/mismatch→exit1. No reportar transpiled JS como cobertura TS por basename. V8 sólo tras conversión oficial fijada Istanbul y receipts de conversión, raw V8 preservado; no parser inventado.

`Combined={combined_id:U,stack:python|istanbul,input_runner_ids:[U],tool_ref:Artifact,receipt_ref:Artifact,raw_report_ref:Artifact,source_manifest_ref:Artifact}`; sólo combinación **oficial** cuando ROOT requiere unión; conservar todos raw de entradas y receta oficial/config/hash. No sumar/mediar porcentajes de platforms ni self merge de counters; diferencias source/pin/config impiden unión. Sin requerimiento union cada plataforma requerida pasa por sí sola. Cada stack/package declarados exact runner_id, nada sin pairing.

### 8.2.1 Construcción acíclica, custodia y verificación por bytes completos

Esta corrección de A02/B01 es **propuesta cerrada previa al gate code**, sin redefinir hashes ni lectores históricos. `H(X)=SHA256(bytes completos finales de X)` y Artifact.bytes es su longitud exacta: incluye todas sus claves y hashes, orden/espacios/newline realmente emitidos. Nada de hash de proyección omitiendo campos, sello preparado presentado como final ni búsqueda de punto fijo. JSON puede escribirse canónicamente D02 para los tree inventories; un Artifact se compara siempre con bytes reales, no con reserialización. Una vez referenciado, X no se edita: cualquier cambio abre corte nuevo y conserva todos bytes/recibos del anterior. Namespace evidence está fuera de árboles fuente y toda resolución aplica Path/containment/no-reparse de §8.1, antes de leer.

Schemas nuevos futuros de soporte, additionalProperties:false, claves todas obligatorias, dominios/nullability de §4/8.1:

- `m3.coverage_classification/1`, K: `{schema_version:1,phase_id:U,base_inventory_ref:Artifact,candidate_inventory_ref:Artifact,entries:[{path:Path,classification:production|test|config|prose|deleted_production,reason:L,proof_refs:[Artifact]}]}`. Entradas exactas para unión de cambios, sin ocultar código por extensión; proof_refs son hechos previos (fuentes/inspección/AST), jamás A/F/I/R ni posteriores. K no contiene aprobación ni su propio hash. Deletedproduction conserva prueba de baja. Excepción de I usa esas pruebas y A como root_approval_ref.
- `m3.coverage_preapproval/1`, A: `{schema_version:1,approval_id:U,phase_id:U,created_at:UTC,contract_ref:Artifact,base_inventory_ref:Artifact,candidate_inventory_ref:Artifact,classification_ref:Artifact,runner_plan_ref:Artifact,policy:Policy,runner_config_refs:[Artifact],tool_lock_refs:[Artifact],root_authorization_ref:Artifact}`. Runner plan es reader `m3.coverage_runner_plan/1`: `{schema_version:1,phase_id:U,entries:[{runner_id:U,kind:runner|combine,stack:python|istanbul,package:Path,tool_ref:Artifact,input_runner_ids:[U]}]}`; runners input=[]; combine entradas anteriores, acíclicas y oficiales. IDs exactos iguales en A/plan/R/P; todos se fijan antes runner. Policy.exceptions.root_approval_ref no puede ser A: A.policy conserva mínimos/scope/rounding con exceptions=[] y K/pruebas describen excepciones pendientes; I.policy añade exactamente esas excepciones usando A ya emitido. No cambiar mínimos. root_authorization_ref es evidencia previa de delegación ROOT bajo control independiente, no este A ni salida futura. A autoriza **insumos por hash**; no afirma F/I/R ni resultados todavía inexistentes. root_ratification_ref de F y root_approval_ref de Exception resuelven este A con ámbito/identidad/decisión reales verificados por ROOT; approved_classification_ref de R refiere K autorizado por A.
- `m3.coverage_execution_observation/1`, E: `{schema_version:1,execution_id:U,phase_id:U,kind:root_inventory|runner|combine,runner_id:U?,upstream_refs:[Artifact],argv:[Text],cwd:Path,environment:[{name:L,value:Text}],started_at:UTC,finished_at:UTC,exit_code:N,stdout_ref:Artifact,stderr_ref:Artifact,tool_ref:Artifact,observed_source_inventory_refs:[Artifact],output_refs:[Artifact],custody_ref:Artifact}`. root_inventory→runner_idNULL; runner/combine→ID fijado en plan. Exit0, argv/env/times/tool/logs y custodia observados se contrastan independientemente; SHA/path/bool por sí solos no acreditan ejecución. custody_ref es evidencia previa o log terminado bajo custodia propia, nunca E ni su futuro receipt; sus refs recursivas también apuntan sólo a artefactos ya terminados. output_refs contiene únicamente outputs terminados de esa ejecución, sin su E/receipt C/R/P/V. ROOT observa directamente la asociación entre ejecución, fuentes, outputs y hashes; no acepta E fabricado por el código evaluado. Ausencias conservan pending, fallos conservan fail conforme §8.3. Ninguna estructura convierte autenticidad en una declaración autoaprobada.

Grafo normativo: `X → Y` significa «X contiene hash/Artifact de Y»; todos los arcos van hacia un orden de creación menor, y se recorre también el cierre recursivo de logs/pruebas/custodia/autorización/config/locks/maps. Ciclo en cualquier cierre se rechaza antes de ejecutar, no basta quitar la arista principal. Graph del caso sin combinación y extensión con combinación:

```text
Leaves = contract, trees/source bytes, proofs, configs, locks, tool,
         prior ROOT delegation/custody, runner plan inputs
K → tree inventories, prior classification proofs
Plan → tools (input_runner_ids son identidades, no hashes futuros)
A → Leaves, K, Plan                 (no F/I/R/E/P/V)
F → A, K, Leaves                    (no I/R/E ni outputs runner)
I → F, tree inventories, proofs, A (no R)
E0 → I, F, A, verification logs/custody
R → I, F, K, E0
Outputs_j → earlier inputs/raw only (no E_j/C_j/P/V)
E_j → R, I, F, Outputs_j, observed inventories/logs/custody
C_j → E_j, I, raw_j, effective_config_j, source_manifest_j
Outputs_c → input raw_j/C_j and earlier pins only
E_c → R, I, F, C_j, Outputs_c, logs/custody
C_c → E_c, I, raw_c, effective_config_c, source_manifest_c
P → R, I, F, C_j, Outputs_j, C_c/Outputs_c if required
V → I, P, helper and earlier proofs (no ref from them back to V)
```

Orden obligatorio de construcción/custodia: (1) ROOT captura árboles fuente completos y artefactos hoja, valida ownership/paths/no-reparse, fija herramientas/configs/IDs/plan/policy y clasifica K; termina primero todo soporte previo de delegación/prueba/log/custodia. (2) Tras revisión independiente de esos insumos exactos emite A; persiste bytes completos antes de calcular H(A). (3) Emite F con A y árboles/K/configs/locks; calcula H(F). (4) Calcula unión/diff e I referido a F/árboles y excepciones aprobadas A; calcula H(I), sin root_receipt_ref. (5) El comando ROOT relee árboles/I/F completos, termina logs/inventarios observados y E0 vinculado a I/F; calcula H(E0). (6) Emite R con H(I)/H(F)/E0/K e IDs fijados; calcula H(R); comprueba independientemente A→K/árboles/config/locks/plan, F→A y E0→I/F/observaciones raw, además de identidades R, ejecución y custodia. Sin aprobación/evidencia ROOT válida no arranca runner. (7) Ejecuta cada runner oficial sobre candidato inmutable/configs preautorizados: persiste primero raw final, summary, effective config, source manifest/maps/test results/logs. Effective config y source manifest nunca refieren su E/C/P. Tras releer árboles/I/F/R y hashes de outputs, ROOT emite E_j y después C_j; calcula ambos hashes completos. C_j.source_manifest_sha256/config_sha256/report_sha256 corresponden a artefactos terminados; E_j vincula R/I/F, output_refs/raw/logs y proceso comprobado independientemente. (8) Si se exige unión, combina oficialmente entradas ya terminadas; termina outputs/logs de combinación, E_c y después C_c (mismo schema receipt, runner_id=combined_id). E_c vincula receipts/raw/source/pins/config de entrada y comando oficial; outputs nunca refieren E_c/C_c. (9) Emite P con root_receipt_ref=Artifact(R), registros completos Runner/Combined y H(I)/H(F), y calcula H(P) completo. Gate relee independientemente bytes/árboles/DAG y contrasta clasificación/aprobación/IDs/config/source/raw/maps/ejecución/custodia; verifica umbrales y ninguna producción omitida, ejecuta helper y emite V al final. Helper no contiene hashes V/P que dependan de él; artefactos anteriores jamás adoptan V. Ninguna autoridad procede sólo de path/SHA/exit/bool, incluso en cadena acíclica. Mutación postfreeze conserva SOURCE_MISMATCH; todas las reglas missing/invalid/exclusion/no-production/branches y exits0/1/2 de§8.3 permanecen intactas.

Para evitar autorreferencias conectadas: E0 puede identificar I/F observados, nunca R (emitido después); preautorización A no certifica H(F) y su soporte de autorización/prueba/custodia no vincula ejecución futura. E_j/E_c pueden vincular raw terminado pero jamás su C/P; C.report_sha256 refiere raw, no P. P contiene R terminado antes de runners; R no contiene sus outputs/receipts/P. Source/raw/maps/summary/effective config/test-result y recibos de soporte sólo refieren insumos anteriores; una arista inversa oculta rechaza todo el DAG. Esta propuesta sustituye I.root_receipt_ref/H(R)↔R.inventory_sha256/H(I), preservando autoridad ROOT y asociación de informes a ejecución independiente real.

**Construcción escalar documental ejecutable, sin ejecución oficial ni conformidad de producto.** El código estándar siguiente materializa en memoria JSON completos de los nuevos schemas K/Plan/A/F/I/R/E0/Ej/Cj/Ec/Cc/P/V, árboles, config/source manifests y raw sintético100/100, con SHA/longitudes de bytes finales reales. Añade combinación para demostrar su cierre acíclico. Fuente/tool/logs/delegación/custodia son fixtures marcados sintéticos: un V.pass ficticio sirve sólo al caso estructural, y ROOT debe rechazarlo como evidencia de ejecución o aceptación de producto. Ningún campo de autoridad se satisface por el literal sintético. La revisión documental puede ejecutar el ejemplo con `scripts/env.ps1` y Python gestionado; no instala nada ni usa GPU/servicio. El generador oficial futuro deberá sustituir hojas sintéticas por bytes oficiales/ejecuciones propias comprobadas y validar todos los dominios, scopes y proofs; aquí se demuestra materialización, claves cerradas y dependencias, no se implementa su validador. Todos los hashes son de bytes completos emitidos una vez y ya inmutables, no de una proyección ni estado preparado.

```python
"""Synthetic documentary JSON fixture; never official runner or ROOT evidence."""
import hashlib
import json

blobs, edges, refs = {}, {}, {}
utc = '2026-10-12T12:00:00Z'
uid = lambda n: str(n).zfill(26)
phase, base_id, candidate_id, runner_id = map(uid, (1, 2, 3, 4))

def emit(name, value, deps=(), raw=False):
    assert name not in blobs and all(d in blobs for d in deps)
    data = value if raw else json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')
    blobs[name], edges[name] = data, tuple(deps)
    path = 'case/' + (name if raw else name + '.json')
    refs[name] = {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return refs[name]

def ref(name):
    return refs[name]

def obj(name):
    return json.loads(blobs[name])

def receipt(kind, name, execution, raw_name, source_name, config_name, identity):
    e = obj(execution)
    return emit(name, dict(schema_version=1, runner_id=identity, phase_id=phase,
        argv=e['argv'], cwd=e['cwd'], environment=e['environment'], started_at=utc,
        finished_at=utc, exit_code=0, stdout_ref=e['stdout_ref'], stderr_ref=e['stderr_ref'],
        tool_ref=ref('tool'), config_sha256=ref(config_name)['sha256'],
        inventory_sha256=ref('I')['sha256'], source_manifest_sha256=ref(source_name)['sha256'],
        report_sha256=ref(raw_name)['sha256'], root_execution_receipt_ref=ref(execution)),
        (execution, 'I', raw_name, source_name, config_name, 'tool'))

def execution(name, kind, identity, upstream, outputs):
    emit(name + '-stdout', b'SYNTHETIC DOCUMENTARY OBSERVATION ONLY\n', raw=True)
    emit(name + '-stderr', b'', raw=True)
    return emit(name, dict(schema_version=1, execution_id=uid(100+len(blobs)), phase_id=phase,
        kind=kind, runner_id=identity, upstream_refs=[ref(n) for n in upstream],
        argv=['documentary_scalar_fixture', kind], cwd='case/candidate', environment=[],
        started_at=utc, finished_at=utc, exit_code=0, stdout_ref=ref(name+'-stdout'),
        stderr_ref=ref(name+'-stderr'), tool_ref=ref('tool'),
        observed_source_inventory_refs=[ref('base-tree'), ref('candidate-tree')],
        output_refs=[ref(n) for n in outputs], custody_ref=ref('prior-custody')),
        tuple(upstream)+tuple(outputs)+(name+'-stdout', name+'-stderr', 'tool',
        'base-tree', 'candidate-tree', 'prior-custody'))

emit('contract', b'SYNTHETIC DOCUMENTARY CONTRACT\n', raw=True)
emit('tool', b'SYNTHETIC TOOL BYTES; NOT AN EXECUTABLE\n', raw=True)
emit('tool-lock', {'fixture_only': True, 'tool_ref': ref('tool')}, ('tool',))
emit('config', b'branch = true\nomit = []\nexclude = []\n', raw=True)
emit('prior-authorization', b'SYNTHETIC NO ROOT AUTHORITY\n', raw=True)
emit('prior-custody', b'SYNTHETIC NO ACTUAL EXECUTION CUSTODY\n', raw=True)
candidate_bytes = ''.join(f'value_{i} = {i}\n' for i in range(1, 101)).encode()
base_bytes = candidate_bytes.replace(b'value_1 = 1\n', b'value_1 = 0\n')
emit('base/src.py', base_bytes, raw=True)
emit('candidate/src.py', candidate_bytes, raw=True)
for name, identity, source in [('base-tree', base_id, 'base/src.py'),
                                ('candidate-tree', candidate_id, 'candidate/src.py')]:
    emit(name, {'schema_version': 1, 'root_id': identity, 'files': [dict(path='src.py',
        sha256=ref(source)['sha256'], bytes=ref(source)['bytes'], kind='regular')]}, (source,))
emit('K', dict(schema_version=1, phase_id=phase, base_inventory_ref=ref('base-tree'),
    candidate_inventory_ref=ref('candidate-tree'), entries=[dict(path='src.py',
    classification='production', reason='EXECUTABLE_SOURCE', proof_refs=[ref('candidate/src.py')])]),
    ('base-tree', 'candidate-tree', 'candidate/src.py'))
policy = dict(line_min=80, branch_required=True, branch_min=80,
    scope='whole_changed_current', rounding='none', exceptions=[])
combine_id = uid(5)
emit('plan', dict(schema_version=1, phase_id=phase, entries=[dict(runner_id=runner_id,
    kind='runner', stack='python', package='pkg', tool_ref=ref('tool'), input_runner_ids=[]),
    dict(runner_id=combine_id, kind='combine', stack='python', package='pkg',
    tool_ref=ref('tool'), input_runner_ids=[runner_id])]), ('tool',))
emit('A', dict(schema_version=1, approval_id=uid(6), phase_id=phase, created_at=utc,
    contract_ref=ref('contract'), base_inventory_ref=ref('base-tree'),
    candidate_inventory_ref=ref('candidate-tree'), classification_ref=ref('K'),
    runner_plan_ref=ref('plan'), policy=policy, runner_config_refs=[ref('config')],
    tool_lock_refs=[ref('tool-lock')], root_authorization_ref=ref('prior-authorization')),
    ('contract', 'base-tree', 'candidate-tree', 'K', 'plan', 'config', 'tool-lock', 'prior-authorization'))
emit('F', dict(schema_version=1, phase_id=phase, created_at=utc, contract_ref=ref('contract'),
    base_inventory_ref=ref('base-tree'), candidate_inventory_ref=ref('candidate-tree'),
    classification_ref=ref('K'), runner_config_refs=[ref('config')],
    tool_lock_refs=[ref('tool-lock')], root_ratification_ref=ref('A')),
    ('contract', 'base-tree', 'candidate-tree', 'K', 'config', 'tool-lock', 'A'))
def root(identity, path, name):
    return dict(root_id=identity, path=path, tree_sha256=ref(name)['sha256'], inventory_ref=ref(name))
emit('I', dict(schema_version=1, phase_id=phase, created_at=utc,
    base_root_ref=root(base_id, 'case/base', 'base-tree'),
    candidate_root_ref=root(candidate_id, 'case/candidate', 'candidate-tree'), source_freeze_ref=ref('F'),
    policy=policy, files=[dict(path='src.py', base_sha256=ref('base/src.py')['sha256'],
    candidate_sha256=ref('candidate/src.py')['sha256'], base_bytes=ref('base/src.py')['bytes'],
    candidate_bytes=ref('candidate/src.py')['bytes'], stack='python', package='pkg',
    classification='production', runner_id=runner_id, exception_ref=None)],
    changes=[dict(kind='modified', old_path='src.py', new_path='src.py',
    old_sha256=ref('base/src.py')['sha256'], new_sha256=ref('candidate/src.py')['sha256'])]),
    ('base-tree', 'candidate-tree', 'F', 'base/src.py', 'candidate/src.py'))
execution('E0', 'root_inventory', None, ['I', 'F', 'A'], ['base-tree', 'candidate-tree'])
emit('R', dict(schema_version=1, phase_id=phase, created_at=utc, base_root_id=base_id,
    candidate_root_id=candidate_id, base_tree_sha256=ref('base-tree')['sha256'],
    candidate_tree_sha256=ref('candidate-tree')['sha256'], inventory_sha256=ref('I')['sha256'],
    source_freeze_sha256=ref('F')['sha256'], approved_classification_ref=ref('K'),
    namespace='case', runner_ids=[runner_id, combine_id], root_execution_ref=ref('E0')),
    ('base-tree', 'candidate-tree', 'I', 'F', 'K', 'E0'))

def outputs(prefix, identity):
    source_name, effective_name, raw_name = prefix+'-source', prefix+'-effective', prefix+'-raw'
    emit(source_name, dict(schema_version=1, runner_id=identity, files=[dict(path='src.py',
        sha256=ref('candidate/src.py')['sha256'], bytes=ref('candidate/src.py')['bytes'], raw_key='src.py')]),
        ('candidate/src.py',))
    emit(prefix+'-effective-raw', b'SYNTHETIC source=whole; branch=true; omit/exclude=[]\n', raw=True)
    emit(effective_name, dict(schema_version=1, runner_id=identity, source_roots=['case/candidate'],
        branch=True, include_patterns=[], omit_patterns=[], exclude_lines=[], ignore_patterns=[],
        test_nodes=['fixture_only'], config_refs=[ref('config')], raw_effective_ref=ref(prefix+'-effective-raw')),
        ('config', prefix+'-effective-raw'))
    emit(raw_name, dict(meta=dict(format=3, version='7.13.1', timestamp=utc,
        branch_coverage=True, show_contexts=False), files={'src.py': dict(executed_lines=list(range(1,101)),
        missing_lines=[], excluded_lines=[], executed_branches=[], missing_branches=[], summary=dict(
        covered_lines=100, num_statements=100, percent_covered=100.0, percent_covered_display='100',
        missing_lines=0, excluded_lines=0, num_branches=0, num_partial_branches=0,
        covered_branches=0, missing_branches=0))}, totals=dict(covered_lines=100,num_statements=100,
        percent_covered=100.0,percent_covered_display='100',missing_lines=0,excluded_lines=0,
        num_branches=0,num_partial_branches=0,covered_branches=0,missing_branches=0)))
    return source_name, effective_name, raw_name

source, effective, raw = outputs('j', runner_id)
execution('Ej', 'runner', runner_id, ['R','I','F'], [source,effective,raw])
receipt('runner', 'Cj', 'Ej', raw, source, effective, runner_id)
source_c, effective_c, raw_c = outputs('c', combine_id)
execution('Ec', 'combine', combine_id, ['R','I','F','Cj',raw], [source_c,effective_c,raw_c])
receipt('combine', 'Cc', 'Ec', raw_c, source_c, effective_c, combine_id)
emit('P', dict(schema_version=1,phase_id=phase,inventory_sha256=ref('I')['sha256'],
    source_freeze_sha256=ref('F')['sha256'],root_receipt_ref=ref('R'),runner_records=[dict(
    runner_id=runner_id,stack='python',package='pkg',platform='documentary_fixture',tool=dict(
    name='coverage.py',version='7.13.1',executable_ref=ref('tool'),lock_refs=[ref('tool-lock')]),
    receipt_ref=ref('Cj'),raw_report_ref=ref(raw),summary_ref=None,config_refs=[ref('config')],
    effective_config_ref=ref(effective),source_manifest_ref=ref(source),source_maps=[],test_result_refs=[])],
    combined_records=[dict(combined_id=combine_id,stack='python',input_runner_ids=[runner_id],
    tool_ref=ref('tool'),receipt_ref=ref('Cc'),raw_report_ref=ref(raw_c),source_manifest_ref=ref(source_c))]),
    ('I','F','R','tool','tool-lock','Cj',raw,'config',effective,source,'Cc',raw_c,source_c))
emit('helper', {'documentary_fixture_only': True})
emit('branch-proof', b'SYNTHETIC AST FIXTURE: 100 assignments; zero branches\n', raw=True)
counter = dict(covered=100,total=100,percent=dict(numerator=10000,denominator=100),minimum=80)
emit('V', dict(schema_version=1,phase_id=phase,inventory_sha256=ref('I')['sha256'],
    reports_sha256=ref('P')['sha256'],helper_sha256=ref('helper')['sha256'],helper_exit=0,
    applies=True,verdict='pass',exit_code=0,files=[dict(path='src.py',change='modified',
    classification='production',source_sha256=ref('candidate/src.py')['sha256'],runner_id=runner_id,
    raw_key='src.py',lines=counter,statements=counter,branches=None,branch_state='not_applicable',
    branch_na_proof_ref=ref('branch-proof'),status='pass',reason=None)],exceptions=[],missing=[],
    ambiguous=[],exclusions=[],stacks=[dict(stack='python',package='pkg',runner_ids=[runner_id,combine_id],
    status='pass')],errors=[]), ('I','P','helper','candidate/src.py','branch-proof'))

def visit(name, active=(), done=None):
    done = set() if done is None else done
    if name in active: raise ValueError('CYCLE')
    if name in done: return
    for dependency in edges[name]: visit(dependency, active+(name,), done)
    done.add(name)

for name, data in blobs.items():
    visit(name)
    assert hashlib.sha256(data).hexdigest() == ref(name)['sha256']
    assert len(data) == ref(name)['bytes']
    if ref(name)['path'].endswith('.json'): json.loads(data)
assert 'root_receipt_ref' not in obj('I')
assert obj('R')['inventory_sha256'] == ref('I')['sha256']
assert obj('P')['root_receipt_ref'] == ref('R')
assert obj('V')['files'][0]['lines']['total'] == 100
# Scalar-domain checks, deliberately independent from future gate/runtime validators.
keys = {
 'K': 'schema_version phase_id base_inventory_ref candidate_inventory_ref entries',
 'A': 'schema_version approval_id phase_id created_at contract_ref base_inventory_ref candidate_inventory_ref classification_ref runner_plan_ref policy runner_config_refs tool_lock_refs root_authorization_ref',
 'F': 'schema_version phase_id created_at contract_ref base_inventory_ref candidate_inventory_ref classification_ref runner_config_refs tool_lock_refs root_ratification_ref',
 'I': 'schema_version phase_id created_at base_root_ref candidate_root_ref source_freeze_ref policy files changes',
 'R': 'schema_version phase_id created_at base_root_id candidate_root_id base_tree_sha256 candidate_tree_sha256 inventory_sha256 source_freeze_sha256 approved_classification_ref namespace runner_ids root_execution_ref',
 'P': 'schema_version phase_id inventory_sha256 source_freeze_sha256 root_receipt_ref runner_records combined_records',
}
for name, names in keys.items(): assert set(obj(name)) == set(names.split())
for identity in (phase,base_id,candidate_id,runner_id,combine_id): assert len(identity)==26
for name, item in refs.items():
    assert len(item['sha256'])==64 and item['bytes']>=0 and '..' not in item['path']
def metric(unit, value, count, state='measured'):
    if state != 'measured': return value is None
    if count <= 0 or value is None: return False
    if unit=='rating': return type(value) is int and 1<=value<=5
    if unit in ('ratio','score'): return type(value) in (float,int) and 0<=value<=1
    return False
assert metric('rating',4,1) and 4>=4
assert metric('rating',3,1) and not 3>=4
for bad in (0,6,4.0,True,None): assert not metric('rating',bad,1)
assert not metric('score',4,1)
assert metric('score',.8,1) and metric('rating',None,0,'indeterminate')
cycles = [('I','R'),('F','E0'),('A','R'),('Ej','Cj'),('Cj','P'),('Ec','Cc'),(source,'Cj')]
for first, second in cycles:
    prior = edges[first]; edges[first] = prior+(second,)
    try: visit(first)
    except ValueError as error: assert str(error)=='CYCLE'
    else: raise AssertionError('cycle not rejected: '+first+'->'+second)
    edges[first]=prior
old_i = {'root_receipt_ref': {'sha256':'0'*64}}
encode = lambda v: json.dumps(v,sort_keys=True,separators=(',',':')).encode()
old_hash=hashlib.sha256(encode(old_i)).hexdigest()
old_r={'inventory_sha256':old_hash}
old_i['root_receipt_ref']['sha256']=hashlib.sha256(encode(old_r)).hexdigest()
assert hashlib.sha256(encode(old_i)).hexdigest()!=old_r['inventory_sha256']
assert 100*80>=80*100 and not 100*79999>=80*100000
manifest = {'documentary_fixture_only':True,'official_execution':False,'production_conformity':False,
 'artifacts':refs,'edges':{n:list(d) for n,d in edges.items()}, 'actual_usage':None,
 'checks':{'complete_json_key_sets':len(keys),'artifacts':len(blobs),'cycles_rejected':len(cycles),
 'A01':True,'A02_B01':True,'100_of_100_structural_case':True}}
print(json.dumps(manifest['checks'],sort_keys=True))
print('DOC only; synthetic sources/raw/tool/ROOT custody; no official execution or T06 closure')
```

Negativos A01: rating humano4 measured válido/min4; rating3 medido/fail; score4 fuera de dominio normalizado; rating0/6/4.0/true inválidos; indeterminate NULL conserva estado; dimensión requerida ausente no pasa aunque las restantes sean5. Negativos A02/B01: I↔R mutuo, F→E0→I→F, A/custodia→R→E0→I→F→A, E_j→C_j→E_j, C_j.report_sha256=H(P) con P→C_j, E_c→C_c→E_c, source manifest→C_j→manifest y modificación de raw completo se rechazan; declarar ejecución verificada sin observación/custodia ROOT independiente nunca pasa. El fixture completo100/100 construido hacia delante acredita estructura/hashes/DAG y falta de autoridad runtime deliberada; fixture no-production y los15 casos§8.4 siguen exigidos en futuros tests de schemas/instrumento. Este test escalar aporta sólo evidencia documental. Ningún umbral se ajusta desde resultados.


### 8.3 Salida exacta, CLI y precedencia exits

CLI futuro **sin cambios** del ledger:

```powershell
. ./scripts/env.ps1
uv run --frozen --no-sync --all-packages python -X utf8 -B "$env:STUDIO_PLUGIN/skills/unit-tests/scripts/coverage-gate.py" $env:M3_PACKAGE --min 80 --changed-only --base $env:M3_PHASE_BASE --json --runner $env:M3_COVERAGE_RUNNER > "$env:M3_PHASE_DIR/helper.json"
$helperExit = $LASTEXITCODE
uv run --frozen --no-sync --all-packages python -X utf8 -B scripts/m3_coverage_gate.py --inventory "$env:M3_PHASE_DIR/changed-inventory.json" --reports "$env:M3_PHASE_DIR/official-reports.json" --helper "$env:M3_PHASE_DIR/helper.json" --helper-exit $helperExit --min 80 --json > "$env:M3_PHASE_DIR/strict-gate.json"
```

ROOT fija base/candidate/phase SHA antes runner, carga entorno gestionado y repite por stack/package. Python runner ledger exacto `uv run --frozen --no-sync --all-packages python -X utf8 -B -m pytest --cov=<raíces producción del paquete> --cov-report=json:<paquete>/coverage.json` y test nodes ratificados, branch/config efectivas congeladas. Jest/Vitest usan binario local ya bloqueado, coverage-final+summary oficial, sin npx/download. Cwd/ruta privada candidata, ninguna medición sobre checkout mutable. `--min` sólo80 admisible para este contrato. JSON stdout completo aunque nonzero; stderr diagnóstico sanitizado, ningún traceback secreto.

`strict-gate.json`, reader `m3.coverage_verdict/1`, exactamente `{schema_version:1,phase_id:U?,inventory_sha256:S?,reports_sha256:S?,helper_sha256:S?,helper_exit:0|1|2,applies:B,verdict:pass|fail|pending,exit_code:0|1|2,files:[FileVerdict],exceptions:[Exception],missing:[Path],ambiguous:[Path],exclusions:[{path:Path,reason:L}],stacks:[{stack:python|istanbul,package:Path,runner_ids:[U],status:pass|fail|pending}],errors:[{code:L,path:Path?,proof_ref:Artifact?}]}`.

FileVerdict exactamente `{path:Path,change:added|modified|deleted|renamed,classification:production|test|config|prose,source_sha256:S?,runner_id:U?,raw_key:Text?,lines:Counter?,statements:Counter?,branches:Counter?,branch_state:measured|not_required|not_applicable|pending,branch_na_proof_ref:Artifact?,status:pass|fail|pending|excepted,reason:L?}`; Counter=`{covered:N,total:P,percent:{numerator:Q,denominator:P},minimum:80}` con Q entero0..100×(2^63−1), numerator=100*covered,denominator=total,covered≤total, comparando100*covered≥80*total. Parsing/cálculo usa enteros arbitrarios exactos, no binary64 para contadores ni overflow de int64 en productos. Sin rounding para decidir ni denominador cero de líneas/statements en producción. No decimal aproximado llamado exacto. Python statements son líneas oficiales misma cuenta; JS guarda ambas. Si required y no hay **ninguna rama real** en el fichero completo, contador oficial0 se conserva en proof/raw, branchesNULL,branch_state=not_applicable y branch_na_proof_ref obligatorio verificado contra mapa/AST completo oficial: no inventar100 %. Config branch off/report sin branches no demuestra ausencia real. Ramas reales>0 exigen ≥80; missing cuando required da pending/fail según raw existente, no N/A. branch_state not_required sólo policyfalse, proofNULL. Archivos deleted/test/config/prosa aparecen excepted con proof; SHA NULL sólo deleted; production vigente sin medición noexcepted.

Exit0: todos whole actuales producción cambiados≥80 en lines/statements y ramas donde requerido; sin fallos/missing/exclusiones/ambigüedades, receipts/raw válidos. Inventario válido sin producción: exit0/applies:false, percentagesNULL, excepciones explícitas completas y reports vacíos válidos (no exigir herramienta para prosa). En esa excepción no-production se conserva diagnóstico helper si existe, sin pedir runner inexistente; CLI argumentos siguen obligatorios y helper ausente/tool2 se declara no aplicable por excepción validada, no cobertura100. Esta única rama tiene precedencia sobre falta de herramientas de cobertura. Exit1 en fase con producción: no conformidad umbral/ambigüedad/source stale/stack incompleto/exclusion/map existente inválido/inventario no reproduce diff/production faltante o denominator0 en raw **existente**; helper exit1 también mantiene fail. Exit2 con producción: herramienta/raw/report/receipt ausente o ilegible/inválido, formato de herramienta desconocido o helper exit2, condición pending. Si hay ambos defectos probados y missing tools, fail/exit1 conserva también errors pending; nunca pass y nunca omitir filas pendientes. Helper exit0 con warning/missing no libera gate; helper JSON corrupto/ausente con producción exit2; salida helper no es medición de producción. Receipt válido no acredita el resultado semántico de tests.

### 8.4 Casos adversos que exigen RED/GREEN después de revisión

| Caso de futuro test | Exit / hecho que debe demostrar el RED causal |
|---|---|
| Archivo70/100/helper promedio85/exit0 | 1; promedio no salva fichero |
| Todos100/100/raw válido/receipt/config/fullinventory | 0; pass eachwhole |
| 79999/100000 mostrado80; frontera80/100 | 1 y0 respectivamente, sin rounding |
| Existing raw sin un archivo producción / raw vacío con producción | 1, missing explícito |
| Tool/raw/receipt inexistente o inválido | 2, pending sin calidad inventada |
| Prosa/config/test-only/deletedproduction con proofs | 0 applies:false, sin porcentaje |
| Changed añadido/untracked/rename/delete/file oculto | Inventario íntegro; current newpath mide; deleted proof; omitted path1 |
| Stack/package/runner faltante o raw aliases ambiguos | 1; ningún path por suffix |
| Omit/exclude/ignore/pragmas/source-map existente defectuoso | 1, nunca medir subset |
| Source SHA staled/bool counters/negative/duplicate IDs/zero denominator | 1; esquema y contadores consistentes |
| Report/receipt/config/raw cambiado tras freeze | 1 si SHA mismatch probado; receipt ausente inválido2 |
| Branch requerido70/100 con line100 / cero ramas reales demostrado | 1 primer caso; cero real N/A explícito/proof sin100fabricado, configuración apagada no acredita N/A |
| JS statement70 con line100 / map TS completo oficial | 1 primer caso; segundo sólo con pairing source exacto |
| Path traversal/reparse/NFC/case collision | 1 antes leer fuera namespace |
| Fixtures documentales fabricadas con scores perfectos | Sólo contrato sintético; no evidencia humana/GPU/audio |

Cada criterio se prueba sólo RED inicial con ausencia/comportamiento causal y luego código mínimo; ROOT pega comandos/salidas originales y SHA por iteración al ledger. No se registra RED musical desde estas tablas ni se escribe instrumento productivo aquí.

## 9. Gates y entrega pendiente

Preparación normativa revisable: schemas cerrados, métodos/units/counts/failure/rights/independencia completos, números propuestos previos a runs, casos adversos e instrumentación reproducible. ROOT debe seleccionar CM-O1/O2/O3 y performance profile, ratificar por SHA y derivar ADR/docs **después** revisión A/B y QA documental. D13 requiere admisión material/asignaciones/anotaciones independientes/actas, no satisfechas por este texto. T06 requiere gate code con RED causal/coverage oficial/review/QA y Verificación completa del ledger; no queda DONE por candidato.

Verificación requerida posterior: lectura integral de contrato y freeze vigente; `uv run --frozen --no-sync --all-packages python -X utf8 -B -m pytest tests/test_m3_coverage_gate.py`; helper+gate estricto por fase §8.3 con inventarios completos/recibos/raw. En esta pasada se entrega estado documental con source freeze SHA/stat/no-reparse/readonly diff; no se ejecuta un fichero de tests inexistente en snapshot como si fuera suite autorizada ni se atribuye pass futuro.

## INICIO ADR_CANDIDATO_T06

# ADR — Cohortes independientes y aceptación por canción/método

Estado: propuesta; número final reservado únicamente por ROOT después revisión. Fecha:2026-10-12. Autoridad: ROOT bajo delegación; esta entrega no adopta ni edita canon.

Contexto: ADR0080/O1 y D02–D05 requieren resultados musicales/visuales vinculados a audio/contexto inmutables; ninguna etiqueta textual, fixture o porcentaje prueba utilidad o conformidad real. D06 tenía cifras parciales de timings/beats; D13 necesitaba fuentes/personas independientes y derechos. T06 incluye instrumento de cobertura strict-phase.

Decisión recomendada: CM-O1, schemas/readers/métodos/casos de este contrato versión1, dos anotadores ciegos y árbitro, aceptación whole por canción/método, errores de palabras y unmatched separados, rubrica completa prefreeze, evidencia por categoría y rights específicos. Performance propuesto N0 max600s/4×duración por perfil completo y recursos libre−1,5GiB; selección/ratificación numérica y pins finales permanecen ROOT. D05 loudness exacto conserva targets y precisión; ningún reader histórico/SQL envelope se amplía. Gate coverage whole ≥80 sin rounding/exclusiones/missing con raw oficial/source freeze/receipts y exits0/1/2 del ledger. Ratings humanos enteros1..5 usan unit=rating, mínimo4 intacto; score/ratio conservan0..1. La cadena acíclica A/F/I/E0/R/outputs/E/C/P/V de §8.2.1 usa SHA de bytes completos y custodia/ejecución ROOT independientes, sin hashes mutuos ni autorreferencias; registro posterior P contiene R, nunca I. Esquemas de aprobación/ejecución se proponen antes de gate code, sin ampliar readers/DTO/SQL históricos.

Alternativas: CM-O2 revisión100% con un anotador; CM-O3 límites más estrictos; performance CM-P2/P3. Coste de adquisición humano mayor en O1, riesgo de falta de material/personas explicitado. Reversible por nueva versión/SHA con nueva evaluación, sin editar resultados pasados.

Consecuencias: no conformidad musical por documentación; métodos dependientes esperan ratificación, product-real espera D13 y capacidades/liberaciones D10/D11/D12. T06 no cierra hasta gate code causal/review/QA y Verificación ejecutada. Material y personas no inventados; original Libro/Libre, audio y consent no se extienden desde un MP3 o declaración de letra. Canon v1/CPUv2/timeline/engine unchanged. No nueva herramienta, licencia, peso, servicio o almacenamiento fuera proyecto.

Validación futura: negativos A01 y A02/B01 y construcción escalar materializable acíclica de§8.2.1, todos los15 casos contractuales de§8.4, TDD causal del gate, raw coverage official completowhole, A/B y QA por SHA; después anotaciones reales y runs/métricas/actas independientes sobre canciones completas, incluyendo Libre4:15 y recovery real. La adopción documental no da pass a esos gates.

## FIN ADR_CANDIDATO_T06

## Apéndice — propuestas de documentos afectados para derivación ROOT

| Documento canónico futuro afectado | Cambio concreto propuesto, sin escritura de este actor |
|---|---|
| docs/decisiones/ADR nuevo e índice | Derivar ADR candidato con unit=rating1..5/min4 y cadena acíclica completa§8.2.1, opción/números/SHA/ratificación, enlazar D06/D13; no reservar número aquí. En esta instantánea ADR0087 e índice readonly conservan bytes anteriores y quedan pendientes de regenerar por ROOT; no afirmar igualdad con el candidato actualizado |
| docs/roadmap/M3/design.md e improvement-plan.md | Sustituir propuestas parciales D06 por referencia al perfil ratificado completo; D13 estado real pendiente personas/material; D07 performance depende ratificación separada |
| docs/roadmap/M3/tasks.md | ROOT único escritor: evidence documental y prereqs faltantes; T06 abierto hasta instrumento/codegate y Verificación, cero false human/gpu passes |
| docs/roadmap/M3/test-plan.md | Ref exacta rúbrica congelada por E2E04/M17/21/25/28/29/31/33/43/49; separar synthetic/audio/render/recovery/human, mantener49CA |
| docs/arquitectura/pipeline-audio.md | Sección evaluación: independiente completa por método, omisión/repetición/unmatched, D05 loudness conservador y letras históricas |
| docs/arquitectura/datos.md / producción futura | Readers nuevos code-first D06 sin mutar D03 outcomes/tablas; interpretación indeterminate dentro payload, no nuevo enum SQL |
| docs/usuario/produccion.md futura / docs/README.md | Guía derechos por uso, incertidumbre karaoke, actas/evidencia y límites admitidos, enlazada desde mapa; no anunciar capacidad pendiente |
| docs/legal/licencias.md | No fila nueva aquí; futuro D10/D11 sólo tras pin/licencia revisados, derechos media específicos separados |
| packages/contracts/ y scripts/tests coverage futuros | Implementación code-first schemas nuevos/goldens y gate con RED causal tras revisión; históricos byteintactos |

Estas propuestas quedan sólo dentro del documento owned. No escribe ADR, índice, ledger, código, manifests públicos, memoria, Git ni usage aggregate.
