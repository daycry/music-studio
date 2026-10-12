# M3/T04 D04 — revisión1 completa, fusión ROOT

ROOT normaliza respuestas íntegras A/B, no transcripción literal. Source48db6312/69274B/baseec7271ba;diff5docs452inserciones/130pins. PF=production-format-contract,PR=request,PD=data,DEP=dependency. A32/B5 completos; conformidadA acotada ante B01, sin falsoverde producto. T04abierta/M3=3/42DOCUMENTAL/functions0.

| CriterioA | Resultado | Evidencia |
|---|---|---|
| T01seams | ✓ documental previo | DEP48–74/tasks120 |
| T01CA01 | ✓ | DEP110–116/PF22 |
| T01CA48 | ✓ | DEP118–130/PF96–107,218 |
| T02campos | ✓ documental previo | PR59–94,130–189/tasks152 |
| T02CA02 | ✓ | PR134–138/PF180,195 |
| T02CA44 | ✓ | PR163–189/PF295 |
| T02CA48 | ✓ | PR154–159/PF129–151 |
| T03migración | ✓ documental previo | PD451–460/PF327/tasks186 |
| T03CA02 | ✓ | PD182–189,228–232/PF180–195 |
| T03CA08 | ✓ documental | PD195–201/PF231 |
| T03CA18 | ✓ | PD182–189,209–219/PF180–191 |
| T03CA20 | ✓ | PD209–219/PF191 |
| T03CA34 | ✓ | PD225–232/PF195,217 |
| T03CA48 | ✓ | PD350–382/PF123,373 |
| T04familias | ✓ documental acotado B01 export | PF96–107,143–149,199–205 |
| T04goldens | ✓ concreción/no verificable ejecución | PF255–283 21normativos;PF203,409 schemas/readers/goldens producto futuros |
| T04ADR | ✓ candidato | ADR85 propuesta/PF401 |
| T04CA12 | ✓ documental | PF229–231 |
| T04CA13 | ✓ documental acotado B01 | PF233–235; codec/reader independiente futuros |
| T04CA18 | ✓ | PF180–191,212 |
| T04CA26 | ✓ documental | PF180–195 |
| T04CA36 | ✓ acotado B01 | PF199–225, cierre debe aceptarSongsinTake |
| T04CA38 | ✓ | PF239–251 |
| T04CA39 | ✓ | PF219–225,251,299 |
| T04CA48 | ✓ | PF96–107,129–151,218,293 |
| scope | ✓ | 5files/tasks201/improvementplan159 |
| Constitución | ✓ | C11,23,33,35,37,43 vsPF76–82,203,229,239–251,293,401 |
| Verificaciónprevias | ✓ evidencia leída | tasks120,152,186;T04abiertaPF407–411 |
| TDDcobertura | ✓ n/a prosa | PF22,411/409;0runtimechange |
| interopOpenAPI | n/a | diff5docs |
| E3docs | ✓ | conv104–108/datos488–492/PF361–377/ADR85index |
| docsstyle | ✗MinorA01 | PF159 frase45palabras/tresobligaciones/regla1docsstyle |

| CriterioB | Resultado | Evidencia |
|---|---|---|
| historiadispatch | ✓ documental | PF90–107,199–223 |
| 7sujetosfieldsets | ✗B01 | ExportprojectmetadataTakeinexistente |
| preparedreceiptDAG | ✓ documental | PF157–159 |
| timeline/rights/remap/límites | ✓ documental | PF4.3–4.9vsD02/D03/ADR74 |
| readersproducto | no verificable | schemas/readersfuturos |

| ID | Grado | Gap | Escenario/Evidencia | Estado |
|---|---|---|---|---|
| A01 | Minor | PF159 frase45palabras/tresobligaciones;docs-style§1≤~25 | preparedImport/Backup agrupa reemplazar execution, omitircampos ypreservarrootrefs | corregir prosa sin cambiar normativo |
| B01 | Important | PF147metadata_refobligatoria;PF233 único readerexigetake_idULID/audio_ref | export_project deSongválidasintomas/letra/portadahistoria;D02PR116 exigeclosure/noTake;Songv1rows.take minItems0/masterNullable. Sólo se podría inventarTake/audio o rechazar cierreválido | confirmadoROOTtextoPR/PF;fixcerradoporoperation |

0Critical/1Important/1Minor, sin deuda/rebate. A verificó130pins/22fixtures/5históricossizesSHA/21vectores12negativos; B130pins+schema take_minItems0/masterNULL/prefijoshistóricos. NoSQL/producto/native/DB/media/GPU/servicios ni writes. HipótesisB importsource→dest no halló igualdadcontradictoria explícita, no esgap ni rebatido; diferencia source/map/dest conservada.

FIX1 ROOTselección rutinaria: mantener campo metadata_ref siempre presente; project_zip lo fija aNULL literal por operación y conserva metadata/letra/portada mediante closure Songv1/SongCPUv2/SongBundleM31. Otros exports que requieren metadata deTake mantienen ByteRef exacto alreaderactual; no generalizarNULL/fallback, noTake/audiofabricado. Alternativa de reader metadata específicoProject es viablepero duplica datos históricos sinnecesidad;O1conservado. Aplicar prepared/final/registry/goldensnegativos/CA36/appendix/ADR coherentes. A01 split3ideas sin cambionormativo. 2026-10-11T21:53:15.020435+00:00
