# D03 — revisión documental, intento1

ROOT normaliza las respuestas completas A1/B1, no transcripción literal. C=production-data-contract.md yT=tasks.md del snapshot M3. Sourcef982b1bd105751B592líneas/diff699líneas4docs/basead69a008a8b60a8ce79aa257a92504676f99293b. A/B frescas secuenciales por4slots: no se afirma ejecución paralela. ✓ documentales, no producto.

| CriterioA | Resultado | Evidencia |
|---|---|---|
| PlanAlembic/upgrade/rollback | ✓ documental | C393–402 |
| FK/index/checks/triggers | ✓ documental | C156–160,366–389;40tablas |
| CA02captura | ✓ documental | C238–254,297 |
| CA02no retarget | ✓ documental | C176,187,201,230–232,384 |
| CA08stemscontroles | ✓ documental | C195–201 |
| CA08reload/audiobytes | ✓ documental | C201,377–378,414 |
| CA18single/composite | ✓ documental | C182–189 |
| CA18audio/duration | ✓ documental | C185–189,209–215 |
| CA20missing/uncertainty/instrumental | ✓ documental | C207–219 |
| CA20correctionevidence | ✓ documental | C209,217–219 |
| CA34presetedit | ✓ documental | C225–230 |
| CA34history | ✓ documental | C230–232 |
| CA48rights/provenance | ✓ documental | C170,241,258–260,327,425 |
| CA48compatibility | ✓ documental | C158,172,217,350,395–400 |
| D02siete/19 | ✓ documental | C303–327;auditor19paresigualD02 |
| FasesCAS/cancel/replay | ✓ documental | C281–301 |
| Gatesexternosfinite | ✓ documental | C260,329–364,459,481 |
| A1estado | ✓ | T156–185/C38,146,406 |
| A2scope | ✓ | T165;4docs/fuera0/avisos0 |
| A3tests/TDD | ✓ prosa | C37,404–431;TDDn/a,PD01..20futuros |
| A4Constitución | ✓ documental | Constitución10–11,18,23,33,35,43/C64–72,174–176,217,327,393–402 |
| A5verificaciónlectura | ✓ candidato | T167/C586;no suplantaadopciónROOT |
| A6generados/OpenAPI | ✓ n/a | diffsólodocs |
| A7docs-style | ✓ | sinviolacióncitable |
| Mapping/extracción | ✓ | 101pins/99actor/source105751Bf982byteexact;datosprefijo29648B |
| Elección/reserva | ✓ | options428b5c/choicec0c651ce;ADR83privadopropuesto |
| SQL/migration/races/readers | no verificable | C154,360,406,431,592;sinruntime |
| E2E/audioGPU/plataforma/M48 | no verificable | futurosdelplan |
| QA/adopción/cierre | no verificable | D03false/T03false/M3=2functions0 |

| CriterioB | Resultado | Evidencia |
|---|---|---|
| Snapshot/diff | ✓ | 101pins0mismatch/C592byteexact/diff699 |
| 40PK/148FK | ✓ | 40tablas,0sinPK/148destinos0unknown |
| Tipos/null/enum/rangos | ✓ | C156–160/G01 |
| Ownership/inversas/scope | ✓ | C174–176,368–389/G04G13 |
| ProyecciónJSONseal | ✗ | C350,354;B01 |
| Armado/sello/children | ✓ salvoB01 | C268–273,377–380 |
| DAG/parents/root | ✓ | C168,197,209,240,374 |
| Single/composite | ✓ | C182–189,215,219 |
| MeasuredAudio | ✓ | C184–189 |
| Stems/mute/solo/silencio | ✓ | C195–201 |
| Analysisbaseline | ✓ | C207–219/models235–245 |
| Timing/tokens/missing/correcciones | ✓ | C209–219,379 |
| Preset/capturedrefs | ✓ | C225–230 |
| Video/timeline | ✓ | C228,232,342,364 |
| Reserva/FKcycles | ✓ | C243–258,375,381 |
| Stages/rawCPUuploadmaintenance | ✓ | C244–260,266,279 |
| CAS/overflow/committed | ✓ | C285–297,381,387,389 |
| CancelACKcrashUNKNOWN | ✓ | C295–301,383 |
| 19pares/7sujetos | ✓ salvoB01 | C269–277,307–327 |
| Importreserved/commit | ✓ | C166,174,275,290,322 |
| Library/restore/jobsinert | ✓ | C323–325,395–400 |
| CapturedRef/readers/gates | ✓ | C329–364/D02:68–81,140–161;no enumgap adicional |
| Additivemigration/rollback | ✓ | C393–402 |
| Snapshot/privacyaftercommit | ✓ | C385–391 |
| PD01..20/SQL/migration/product | no verificable | C404–431;noejecutados |

| ID | Grado | Gap | Escenario | Estado |
|---|---|---|---|---|
| B01 | Important | Discriminantes incompatibles en JSON kind | C350/354/356 exige todascolumnasroot+kindseal. Audio.kindmaster vssealkindaudio; sourceasset/rights/lyrics/preset/result dominios disjuntos(C169/170/182/185/225/269). Overwritepierderoot;duplicarkeyrechaza. G09 impide seal/consumo | confirmado porROOT;FIX1fresco |

0Critical/1Important/0Minor, sinrebates. A29criteriossin gapsconformidad y routing aB confirmado. B25criterioscompletos; no gap extraCapturedRefkind: outerD02enum separado de familiasinternas. No ampliar hallazgo preliminar a defecto.

Aauditoresstdlibstdin managedPythonexit0:101pins/99actor/40tablas/19pares7sujetos/source/extracción/prefijo/ADRmetadata; regexrender_n0/delimitadores propio corregidos. Bstdlibstdin managedPythonexit0:6colisiones JSON/dupkeyreject/101pins0mismatch/40PK/148explicitFK0unknown/14guards/20futuretests; primerregexUnicodeWindowsstdinexit1corregido. LentesnoneSQL/ORM/appimports/DB/media/native/GPU/servicios/DockerWSL/install/escrituras. Ledger0/40avisosChangelog de tareasabiertas;scope4docs/fuera0avisos0/CfalseDfalse. NoQA/adopción/cierre ni nativegrants.

ROOTelige FIX1 mínimo semántico: campoJSON reservado `seal_kind` para el tipo de m3_seal, preservando `kind` de root cuando existe. OuterCapturedRef.kind/schema ySQLcolumnas/baseline/históricos intactos. Debe definir unicidad/reservednamespace/extras/versions/proyección/reader/G09/exemplospositivosnegativos/todasfamilias y apéndice/ADR candidatos coherentes antesreview2. No resolver conaliasheurístico/dupkeys/overwrite/defaults ni introducir versiónhistórica ampliada. 2026-10-11T20:11:41.906146+00:00
