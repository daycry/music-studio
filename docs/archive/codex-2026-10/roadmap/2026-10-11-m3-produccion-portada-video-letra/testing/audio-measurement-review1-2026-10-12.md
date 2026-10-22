# Revisi?n1 ROOT ? D05

FULL60A/34B. A0gaps;B2Important B01rights_ref/B02absenceStates. C/Dauto false;scope4/0/0. T05 vuelve enprogreso paraFIX1, noQA/adopci?n. Metadataomitindicio no gap (refs noigualdadexpl?cita). Historiacapacityretry/harnessstdoutpreservada.

# Lente A — intento1, persistencia ROOT del retorno readonly

Actor `/root/review_m3_d05_a1`: DONE, 0Critical/Important/Minor. Revisión documental únicamente, no ratificación ni QA. ROOT normaliza las tres tablas completas (13+25+22=60 filas), sin convertir aceptación de producto pendiente en verde. C=audio-measurement-contract.md del snapshot141pins.

| Criterio T05/objetivo | Estado | Evidencia del actor |
|---|---|---|
| Objetivos−14/−23/−16 y tolerancias | ✓ documental | C65–71, streaming/podcast±0,5,broadcast±0,2QC; presets propios no norma universal |
| TP≤−1,suma<−30,mix≤1frame/residual<−60 | ✓ documental | C83,95,97,109–115 intervalos, strict,bordes/silencio |
| Sin limitador oculto | ✓ | C119–123,220 limiterdisabled/estático sinfallback |
| CA07 separación alineada/suma/escucha | ✓ concreción | C91–101 roles4/FsC/origenN/offset0/ventanas/escucha obligatoria |
| CA10 reproducción/mezcla | ✓ concreción | C105–115 gains/mute/solo/captura/oracle/lag/bordes/clipping/seek |
| CA11 final/formato | ✓ concreción | C119–137 finaldecode completo/LUFS/TP/formato/delay/padding/reader |
| CA12 original/ZIP48k | ✓ concreción | C99–101,125,133–137,196 originales/sidecar/4PCM24/gain1/hashes |
| CA14 no conforme/evidencia/original | ✓ concreción | C121–125,155,200,231–243 intentos/partials/no serving/padre intacto |
| Subtarea contrato/casos/alternativasSHA | ✓ | C18–35,251–278 AMO1/2/3/22vectors/source07767756/80070B |
| Subtarea campos/métricas/derivados | ✓ preparación | C139–247 ADR/pipelineexact4pieces |
| Ratificación/gates/QA/Changelog final | no verificable pendiente | tasks232,244–255 enrevision/checks abiertos,C342 |
| Verificación literal T05 ratificada | no verificable pendiente | tasks240,C342/report preparación nofinal |
| Aceptación producto CA07/10/11/12/14 | no verificable pendiente | C12,97,115,249,253,338/plan232–239 tareas reales dependientes |

| Transversal/sección | Estado | Evidencia del actor |
|---|---|---|
| Scope4/0/0 runtimeDTO/SQLintactos | ✓ | prepare.scope/status/diff4docs |
| TDD entrega | ✓ n/a prosa | C12,143,342 REDantesimplementación/liberacióntrasconformidad |
| Interop/OpenAPI/cobertura | ✓ n/a | No código/hooks/API, plan delimita,nocobertura inventada |
| §1 opciones/D02/03/04 | ✓ | C16–24 AMO1delegada/O2historia/readersfuturos |
| §2 pin/probes/atribución/plataforma/licencia | ✓ | C28–37 seisprobesanteriores propios0/interfaz≠precisión Windows≠Linux |
| §3 PCM/frames/subnormales | ✓ | C41–47,159–163 f64le8NC/Nporcanal/hashantesflush/NULLpairs/nonfinite |
| §4 RMS/peak/dBFS/clipping/silencio | ✓ | C51–55 units/contadores/ratio>.005/silence≤.001 |
| §5 K/gating/bloques/cola/EOF/targets | ✓ | C59–73 strict>/J/F/completos/cola/insuficiencia sinIficticia |
| §6 impresión/algoritmo/límites | ✓ | C77–87 incertidumbres/calibración/pin/plataforma/noTP−1,1porlog |
| §7 stems/alineación/conversión | ✓ | C91–101 global/canal/últimaventana/ties-even/rango/LSB/noclamp |
| §8 mixer/transporte/bordes | ✓ | C105–115 yD03195–201 controles sellados silenciointencional |
| §9 tratamiento/finalcodec/tags/original | ✓ | C119–137 max2sobreoriginal/readerindependiente |
| §10 payload17/seis métodos/4states | ✓ | C149–155,187–202 METHODS6/STATES4; exact sóloMetric |
| §10 refs/11perfiles/17errores | ✓ | C147,212–231 PROFILES11/ERRORS17/D02D04refstyped |
| §10 D05errorvsD02receipt | ✓ | C123,229–231,D02171 mappingPRODUCTION_NOT_CONFORMANT sinAPIchange |
| §10 fallosparciales/NULL | ✓ | C159–200,233–243 parejas AO/output/Format/Tags/attempts reales |
| §10 finalaudio/timing/features/scene | ✓ | C206–208,D03185–189,D04192–205 samebinding/fields intactos |
| §10 rights/privacy/historia | ✓ | C247–249 conjunciónrights/rawprivado/history/hashnoauthority |
| §11 vectors22 | ✓ documental | C251–280 IDsúnicos0executados |
| §12 ADR/pipeline/index/history | ✓ | extractionADRbodyequal/pipelineprefixexact+appendixequal/index129propuesta |
| Constitución local/server/engines | ✓ | C318/constit16,31–33 local/engineraw/serverpost |
| Constitución canción/linaje/inmutabilidad | ✓ | C125,206–208,247/constit18–19,39 CPUhijo/CAS/originales |
| Constitución honestidad/codefirst/estado/rights | ✓ | C12,143,155,247,342/constit21,65,69,84 nocapabilityliberada/readersfuturos |
| Incidentes roles preservados | ✓ lectura | report/freeze mantienen DENY/READONLY/genérico noALLOWdeotros |
| Integridad final | ✓ | 141pins0diff treschecks/4candidateSHA/nofileswritten |

Los siguientes ✓ acreditan especificación, no señales ejecutadas.

| Vector | Estado | Evidencia |
|---|---|---|
| AV01 | ✓ | C257 mono/stereo/N/EOF/layout/stream/parcial |
| AV02 | ✓ | C258 PCMextremos/float/NaNInf/overflow/parciales |
| AV03 | ✓ | C259 subnormal/flushanálisis/hashoriginal |
| AV04 | ✓ | C260 ceroNULL/N0/umbral.001 |
| AV05 | ✓ | C261 silencio/order/no channeldup/swap |
| AV06 | ✓ | C262 abs1/>1/frontera.005/clippingnormalized |
| AV07 | ✓ | C263 tasas/layout/NB/H/strict/EOF/tail/no paddingI |
| AV08 | ✓ | C264 noestacionariacompleta/nofavorablewindow/promedioLUFS |
| AV09 | ✓ | C265 cotastotales/calibradas/targets/incertidumbre |
| AV10 | ✓ | C266 broadcast±.2/TPtolerancenopinclaim |
| AV11 | ✓ | C267 parser/locale/units/EOF/Linuxacreditationpropia |
| AV12 | ✓ | C268 set4/sumaδ0/NFsC/offsetnegatives |
| AV13 | ✓ | C269 relative strict/canaldébil/window |
| AV14 | ✓ | C270 silence/absolute/denominator0/noepsilon |
| AV15 | ✓ | C271 gains/multisolo/mute/any_solo muted |
| AV16 | ✓ | C272 lag−1/0/+1/overlap/borders/channels/residual/ambiguity |
| AV17 | ✓ | C273 intentionalsilence/capturepeak/no fakelag |
| AV18 | ✓ | C274 ties±/int24/LSB/ringingoverrange |
| AV19 | ✓ | C275 common44.1→48/conversionactual |
| AV20 | ✓ | C276 original/sidecar/embeddedincompatible/padre |
| AV21 | ✓ | C277 codecfinal/postcodecTP/delay/tags |
| AV22 | ✓ | C278 unions6/states4/refs/rights/partials/max2real |

Evidencia ejecutada readonly: gitstatus/stat/diff4files398insertions; diff completo342líneasC leído;141SHAantes/después/final0diff; derivationADRbody_equal ypipelineprefixexact27677→34048B+appendix_equal; diffSHA728df10c95177c3ff4203302e3bc1f629e74222f2ff906a6676ce952a12647fb currentequal; countsMETHODS6/STATES4/ERRORS17/PROFILES11/VECTORS22; knowledge-find exit0sinaciertos. Check30anterior sólo leído, no propio.

Primarias contrastadas por actor: ITU BS1770-5 PDF; EBU R128v5_0.pdf2023 (genericURLfalló, versiónexplícitaaccesible); FFmpegfilters/loudnorm ysource7.1histórico sincertificaciónpin9. Audio/AV/probes/native/GPU/media/escrituras propias0. No hallazgos fuera lente ni cierre. Fuente del informe: mensaje finalreadonly del actor, no supuesto archivo creado por él.


# Lente B — intento1; persistencia ROOT del retorno readonly

Actor `/root/review_m3_d05_b1`: 0Critical/2Important/0Minor. C=contratoaudio del snapshot141pins, source07767756/80070B. Tabla completa34filas, no QA ni aceptación de producto.

| Criterio | Estado | Evidencia |
|---|---|---|
| Dominio Fs32/44.1/48k C1/2 identidad | ✓ | C41,D03198 |
| Archivo/PCMhash/f64le completo | ✓ | C43–47,161 |
| Subnormales original/análisis | ✓ | C45–47/AV03259 |
| NaNInf/overflow/decodeparcial | ✓ | C45,159–163,236–237 |
| RMS/peak agregado/canal/cero | ✓ | C51,165,169 |
| Clipping float/rail/M0>.005 | ✓ | C53/AV06262 |
| Silencio≤.001/mixerintencional | ✓ | C55,113–115 |
| K/monoL/R/gatesstrict | ✓ | C59/ITUeq2–7 |
| Bloques H/B/J/F/cola tresFs | ✓ | C61/15cases scalar exit0 |
| TPfulltail/EOFindependiente | ✓ documental | C61,79–81 pendienteactual |
| Audio breve/sentinel/originalfailed estados | ✗ B02 | C63/238vs87;196/242vs235 |
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
| Original sinmedidas/comparaciónbytes | ✓ éxito | C125,196 excepciónfailedB02 |
| Snapshotrights family/reader refadmisible | ✗ B01 | C147/153,D0281,D03414 |
| Max2/gaindestática/finalcodec | ✓ | C119–123,195,200 |
| ErrorprivateD05→D02enum | ✓ | C123,229–231,D02171 |
| PCM24/resample/set4 | ✓ documental | C99–101,194,219–223 |
| Tags/formato/delay/readerreal | ✓ documental | C135–137,202,D04243–249 |
| Finalaudio/timing/features/fieldsintactos | ✓ | C206–208,D03185/228,D04192–200 |
| ADRpropuesto/M0/history/vectors0 | ✓ | C12,24,253,284,342/ADR2 |
| Derivados/prefixbyteexact | ✓ | ADRbodyequal/pipelineprefix+suffixequal |
| Precisión/audio/codec/transporte/escucha | no verificable | Futurosgates,0audio/native/FFmpeg/services |

| Gap | Grado | Escenario |
|---|---|---|
| B01 | Important | C153 requiere rights_ref CapturedRefD02exact. D0281 family enum excluyerights; snapshotgenuino production.rights/1 D03414 exige familyrights. Retagrevision/measurement infringeD03;NULL falta rights noéxito. Referenciagenuina no cabe en captura obligatoria. |
| B02 | Important | C87vs63/238: Fs48k/N19199, decodefinito completo/resumensentinel−70porfaltabloques requiereindeterminate/INSUFFICIENT_FRAMES yfailed/missing simultáneamente. C235vs196/242: originalSOURCE_MISMATCHantesdecode obligaMetricunavailable/gateindeterminate y4Metricnot_requested/gatenot_requested a la vez. Estadosdisjuntos sinprecedencia/excepción. |

Indicio metadataomit **no gap**: noigualdadexplícitaM.metadata_ref==Tags.metadata_ref, capturasexternasD05dependencies pueden conservarD04. No reinterpretar este indicio como defecto aprobado ni ocultar rebate.

Evidenciareadonly:141SHAantes/después/final0diff/4candidateSHA/source80070B;10manifestmembersbytesSHA yoriginal0d9d0759intacto; ADRbodyexact/pipelineprefixsuffixexact/indexsolounaentrada86; diff429lines/4files398adds0deleteSHA728df10c95177c3ff4203302e3bc1f629e74222f2ff906a6676ce952a12647fb; scalar15H/B/J/F/cola+δborders/energyexit0 e interseccionesstates=[]; knowledge-find0sinaciertos. Primercomandocp1252stdoutexit1 conservado, relecturaUTF8exit0, sinwrite.

Primariasporactor: ITU1770-5PDF; EBU R1282023; sourceFFmpeg7.1histórico+commit51c4a23d74libavfilter/f_ebur128.c. Consulta no conformidadbinaria. Primerturnocapacityerror noveredicto/artefactos, reintentomismoactor sincontarsegundarevisión. Escriturasactor0,ROOTpersiste mensaje final. Nofinalratification/QA/cierre.
