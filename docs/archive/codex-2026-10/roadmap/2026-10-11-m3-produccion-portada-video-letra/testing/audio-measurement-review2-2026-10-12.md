# Revisión2 ROOT — D05 A/B sin gaps actuales

FULL60A/34B; B01/B02Important originales conservados como corregidos; no nuevosgaps. C/Dauto false/scope4/0/0. TresA no-verificables ratificación/gates/QA/Changelog,Verificación ratificada yproducto real siguenpendientes. Metadatamodeomit indicio NOgap. Fuente15608698/94564B; aplicación0.

# Lente A — revisión2/3, persistencia ROOT del retorno readonly

FULL60 (13T05+25transversal+22AV). 0Critical/Important/Minor. Tres filas noverificables pendientes preservadas. NoQA/ratificación/productclosure. Fuente15608698/94564B; snapshot141pins4docs. C=audio-measurement-contract del corte actual.

| Criterio | Estado | Evidencia actualA2 |
|---|---|---|
| Objetivos−14/−23/−16 y tolerancias | ✓ documental | C65–71 presets propios ±.5/±.2QC,nocertificaciónpin |
| TP/suma/mix límites | ✓ documental | C83,95,97,109–115 intervalosstrict/bordes |
| Sin limiter oculto | ✓ | C119–123,220 disabled/static/no fallback |
| CA07 stems/escucha | ✓ concreción | C91–101 roles4/FsCN/origen/offset0/ventanas/escucha real pendiente |
| CA10 reproducción/mix | ✓ concreción | C105–115 controls/capture/oracle/lag/borders/silence/seek |
| CA11 final/formato | ✓ concreción | C119–137 decodefinal/LUFS/TP/delay/padding/tags |
| CA12 original/ZIP48k | ✓ concreción | C99–101,125,133–137,196 bytes/sidecar4PCM24/gain1/hashes |
| CA14 no conforme/evidencia/original | ✓ concreción | C121–125,155,200,233–258 realattempts≤2/no serving/overwrite |
| Subtarea contrato/casos/opcionesSHA | ✓ preparación | C18–37,266–295 AMO1/2/3/pin/22vectors/currentSHA |
| Subtarea campos/métricas/derivados | ✓ preparación | C139–262,301–355 cuatroderivativescoherentes |
| Ratificación/gates/QA/Changelog | no verificable pendiente | T232,244–255/C7,12,299,357 abiertos/propuesta |
| Verificación literal T05 ratificada | no verificable pendiente | T240/C357 preparatoria no ratificaciónfinal |
| Aceptación real CA07/10/11/12/14 | no verificable pendiente | C12,97,115,264,268,353/P232–239 futureproduct |
| Scope4/0/0 runtimeDTO/SQLintacto | ✓ | prepare.scope+own diff4/exclusionesvacías |
| TDD prosa | ✓ n/a | C12,24,143,333,357 REDpreviofutureimplementation |
| Interop/OpenAPI/cobertura | ✓ n/a | Sólo docs no código/hooks/spec/no coverageinventada |
| §1 opciones/D02/03/04 | ✓ | C16–24 O1/O2historia/readersfuture/no envelopeschange |
| §2 pin/probes/atribución/plataforma/licencia | ✓ | C28–37 previous6probes/own0/interface≠accuracy/Linuxindependent |
| §3 PCM/frames/subnormales | ✓ | C41–47,159–163 f64le8NC/hashbeforeflush/nullpair/nonfinite |
| §4 RMS/peak/dBFS/clipping/silencio | ✓ | C51–55,165,169 units/counters/ratio>.005/RMS≤.001 |
| §5 K/gates/blocks/tail/EOF/targets | ✓ | C59–73 strict>/J/F/tail/absencewithoutI |
| §6 print/algorithm/límites | ✓ | C77–87,175–177 bounds/calibration/pin/platform/EOF/notlogalone |
| §7 stems/alineación/conversión | ✓ | C91–101 global/channel/lastpartial/tieseven/range/LSB/noclamp |
| §8 mix/transporte/bordes | ✓ | C105–115,183–185/D03195–201 controls/lag/silence |
| §9 tratamiento/finalcodec/tags/original | ✓ | C119–137 max2original/actualfinal/independentreader |
| §10 payload17/methods6/states4 | ✓ | C149–155,187–202 actual17/6/4/exactonlyMetric |
| §10 refs/perfiles11/errores17 | ✓ | C147,212–231 actual11/17/RightsSnapshotRefseparateD0281D03414 |
| §10 D05errorvsD02receipt | ✓ | C123,229–231/D02171 privateerror→PRODUCTION_NOT_CONFORMANT |
| §10 partials/NULLs | ✓ | C159–200,233–258 precedence/method/fase/originalnot_requested |
| §10 finalaudio/timing/features/scene | ✓ | C206–208/D03185–189,228 finalbinding/fieldsintact |
| §10 rights/privacy/history | ✓ | C147,153,262–264 genuinesnapshot/ANDrights/rawprivate/history |
| §11 vectors22 | ✓ documental | C266–295 IDsunique/audiotests0 |
| §12 ADR/pipeline/index/history | ✓ | C301–355 ADRbodyexact/pipelinebaseSHA+appendixexact/86proposed |
| Constitución local/server/engines | ✓ | C333/K16,31–33 local/raw/serverpostpublish |
| Constitución canción/linaje/inmutabilidad | ✓ | C125,206–208,262/K18–19,39 CPUchild/CAS/originals |
| Constitución honestidad/codefirst/state/rights | ✓ | C12,143,155,262,357/K21,65,69,84 nocapability/fakecapture |
| Incidentes roles preservados | ✓ lectura | implementation-report5,7 DENY/READONLY nofakeALLOW |
| Integridad final | ✓ | Own141SHA0diff/4candidates/rightSHA/write0 |
| AV01 | ✓ documental | C272; mono/stereo/N/EOF/layout/partial |
| AV02 | ✓ documental | C273; PCMfloat/NaNInf/overflow/partial |
| AV03 | ✓ documental | C274; subnormalsonlyanalysis/minnormal/originalhash |
| AV04 | ✓ documental | C275; zeroNULL/N0/RMS.001 |
| AV05 | ✓ documental | C276; silence/order/swap/duplicate |
| AV06 | ✓ documental | C277; abs1/>1/ratio.005/normalizedclip |
| AV07 | ✓ documental | C278; Fs/layout/HBJF/tail/N19199/TPfullEOF |
| AV08 | ✓ documental | C279; nonstationaryfull/nofavorablewindow/avgLUFS |
| AV09 | ✓ documental | C280; totalbounds/targets/uncertainty |
| AV10 | ✓ documental | C281; broadcast±.2/unprovenalg/normnotpin |
| AV11 | ✓ documental | C282; parser/locale/EOF/−70ambiguous/toolreal/Linux |
| AV12 | ✓ documental | C283; roles4/δ0/NFsC/offset |
| AV13 | ✓ documental | C284; strictratio/weakchannel/window |
| AV14 | ✓ documental | C285; absolutesilence/denominator0/lastpartial/noepsilon |
| AV15 | ✓ documental | C286; gain/multisolo/mute/any_solo |
| AV16 | ✓ documental | C287; δ−1/0/+1/overlap/edges/channels/residual/ambiguity |
| AV17 | ✓ documental | C288; intentionalmute/capturepeak/nofakelag |
| AV18 | ✓ documental | C289; PCM24ties±/LSB/range/ringing |
| AV19 | ✓ documental | C290; common44.1→48/N/offset/measuredFs |
| AV20 | ✓ documental | C291; original/sidecar/incompatibleembed/preservedparent |
| AV21 | ✓ documental | C292; finalcodec/postcodecTP/delay/tags |
| AV22 | ✓ documental | C293; sixunions4states/rights/originalfailednot_requested/metadataomit/max2 |

| Gap anterior | Grado anterior | Veredicto actualA2 | Evidencia |
|---|---|---|---|
| B01 | Important | Corregido documentalmente; B2 independiente pendiente | C147,153,262,293,323,351 RightsSnapshotRefD05tipo4keys/familyrights/production.rights1/SHA; D0281intacto/D03414coincide, no retag/NULLconsumed |
| B02 | Important | Corregido documentalmente; B2 independiente pendiente | C63,87,196,233–258,278,282,293,323,337,351 method/fase; N19199→indeterminateINSUFFICIENT_FRAMES; original4Metric/Precision/Gatenot_requested evenfailed; log−70 aloneambiguous |
| Metadataomitindicio | No fue gap | No reabierto | C202,223,293,351 transporteomitido/capturaD04independent,D04247intacto |

Ejecución propiareadonly A2:141pins0diff4candidates;diff112273B/SHA00daf52cdb3a024d3532bc4947151556b055bf6c997fcc26bfa827effec143e9; ADRbodyexact/pipelinebaseSHA+appendixexact;17fields6methods4states17errors11profiles22AV; scalar15/15HBJFtail (Fs48kN19199→B19200/J0/F0/tail19199). Knowledge-find exit0sinaciertos. 43actorchecks/14docspec leídos, no runtimeown43. ITU1770-5 yEBUR1282023primarias contrastadas no binaryconformance. Source141beforeafter inmemory sinwrites; noaudio/native/GPU/services/deps/Git propios. B2fresh aúnpending. Actorfinalmensaje es fuente, ROOTnormaliza íntegro60table/3pendientes, no supuestoarchivoactor.


# Lente B — revisión2/3; ROOT normaliza retorno readonly fresco

FULL34criteriosB preservados;0Critical/Important/Minor. Las32filas previamenteconformes se reevalúan y dos defectos resueltos;funcionesmedia reales siguen noverificables. Source15608698/94564B/357líneas.

| Criterio | Estado | Evidencia actualB2 |
|---|---|---|
| Dominio Fs32/44.1/48k C1/2 identidad | ✓ | C41,D03198 |
| Archivo/PCMhash/f64le completo | ✓ | C43–47,161 |
| Subnormales original/análisis | ✓ | C45–47/AV03259 |
| NaNInf/overflow/decodeparcial | ✓ | C45,159–163,240–241 |
| RMS/peak agregado/canal/cero | ✓ | C51,165,169 |
| Clipping float/rail/M0>.005 | ✓ | C53/AV06262 |
| Silencio≤.001/mixerintencional | ✓ | C55,113–115 |
| K/monoL/R/gatesstrict | ✓ | C59/ITUeq2–7 |
| Bloques H/B/J/F/cola tresFs | ✓ | C61/15cases scalar exit0 |
| TPfulltail/EOFindependiente | ✓ documental | C61,79–81 pendienteactual |
| Audio breve/sentinel/originalfailed estados | ✓ B02 corregido | C63,87,196,233–258 precedenceoriginal/fase |
| Targets/broadcast±.2 | ✓ | C65–71/EBUR128h/i |
| Print/alguncertainties | ✓ | C79–85,175–177 |
| TP−1.1 no prueba | ✓ | C81–83 |
| Linearpeakmetadata no dB | ✓ | C77,85/FFmpegsourcehistórico+commit |
| Ratiosestrict<1e−3/<1e−6 | ✓ | C95,113/scalar−30/−60 |
| Silenceabsolute≤1e−6 sinratio | ✓ | C97,183/AV14270 |
| Ventanas/canal/últimaparcial | ✓ | C95,113,183 |
| δsign/overlap/edges | ✓ | C109/scalarδ−1/0/+1 |
| BordesRMS/peakgates | ✓ | C109,185 |
| Lagúnico/canal/ambiguity | ✓ | C111/AV16272 |
| Mute/solo/gain/no pan | ✓ | C105,D03198–201 |
| Métodos6/perfiles11/states4/errores17 | ✓ estructura | C153,189–196,214–229 countsactual |
| Input/outputpartials/decodePCMpair | ✓ | C159–163,198–202 |
| Original sinmedidas/comparaciónbytes | ✓ todas ramas | C125,196,246,256 originalnot_requested inclfailed |
| Snapshotrights family/reader refadmisible | ✓ B01 corregido | C147,153,262,D0281intacto,D03365/414/418 exactRightsSnapshotRef |
| Max2/gaindestática/finalcodec | ✓ | C119–123,195,200 |
| ErrorprivateD05→D02enum | ✓ | C123,229–231,D02171 |
| PCM24/resample/set4 | ✓ documental | C99–101,194,219–223 |
| Tags/formato/delay/readerreal | ✓ documental | C135–137,202,D04243–249 |
| Finalaudio/timing/features/fieldsintactos | ✓ | C206–208,D03185/228,D04192–200 |
| ADRpropuesto/M0/history/vectors0 | ✓ | C12,24,264,268,305,325,353,357/ADR2 |
| Derivados/prefixbyteexact | ✓ | ADRbodyequal/pipelineprefix+suffixequal |
| Precisión/audio/codec/transporte/escucha | no verificable | Futurosgates,0audio/native/FFmpeg/services |

| Gap histórico | Grado previo | Veredicto actual | Evidencia actual |
|---|---|---|---|
| B01 | Important | corregido | C147,153,262 RightsSnapshotRef cuatrokeys familyrights/production.rights1/SHA sellado+owner/scope/cierre;D0281ochofamiliesintactas/D03414rights; no retag/NULLconsumed |
| B02 | Important | corregido | C63,87,196,233–258 Fs48kN19199→indeterminateINSUFFICIENT_FRAMES/J0F0/Iinsufficient_framesNULL;TPindependiente. OriginalSOURCE_MISMATCH/RIGHTS_REQUIREDglobalfailedpero4Metric/Precision/Gatenot_requested;−70roundedalone→PRECISION_UNPROVEN;realerror→TOOL_FAILED |

Metadataomit indicio NOgap1/2; M.omittransport, D04capture/readingindependent/noM.ref=Tags.refimpuesta. Nuevosgaps0. IndependienteB2real:141pins0diff;4docs413adds0delete/diff112273B SHA00daf52cdb3a024d3532bc4947151556b055bf6c997fcc26bfa827effec143e9 igualsource.diff; ownscalar15HBJF/3δedges/energy/ties/muteSolo/8textpredicatesB01B02true, counts17fields6methods11profiles4states17errors22AV. ADRbodyexact/pipelineprefix27677B+appendixexact total35245B/indexsólo86propuesta. Knowledge-find0sinaciertos. Incidentesstdoutcp1252/assertUnicode yexploraciónautocrlfEOL preservados, relecturaUTF8 ydiffordinarioexact0sin sourcewrites.43actorchecks14spec sóloleídosatribuidos,0audioruntime/probes/native/GPU/services/deps/writes. PrimariasITU1770-5/EBUR1282023/FFmpegfilters contrastadas,no prueba binaria. NoQA/ratificación/cierre,3filasA pendientes. ROOTpersistemensajefinalreadonly, tablaFULLnoartefactoactorinventado.
