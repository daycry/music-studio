# M2/T05 congelación del legado — revisión1 A/B/D sin gaps

ROOTnormaliza43A/14B/6D completos; ninguna aprobación integra fullT05. Cauto false,Dauto true por4routesmigrations; scope6/0fuera/0avisos. A1propio23PASS/217pins/44imports/27tables356colscomparadas, B1propio23+43PASS/217pins44/48imports/ASTcodecs/DDLs/headsfixturepopulated; D1memoriaSQLsolo loadprobesmedidosnoproducción. 0Critical0Important0Minor actuales. QAactualfinaltestSHA pendiente.

# M2/T05 legado2A — LenteA1 completa, B/D pendientes

ROOT normaliza43A íntegros del reviewer freshA1. No gapsAactuales;Brobustez yDperformance todavía vivos. NoQA/CAS/closurefullT05.

| CriterioA | Resultado | Evidencia |
|---|---|---|
| diff complet | ✓ | 6sources5runtime1test4blocks |
| ownership/scope | ✓ | tasks207/1514/1519/1522 scope6/0/0 |
| scopehistoric | ✓ | scope-before-ROOT-declaration.json noexclusions |
| MIG01 head0006 | ✓ | test78[0006] |
| MIG01 head0007 | ✓ | test78[0007] |
| futurebeforeload | ✓ | test21/48 newtablecolumnbeforeallreloads |
| staticregistry | ✓ | registry86 27literals noappmodels/reflection |
| columnsorder | ✓ | 27tables356cols0diffM1sealed |
| typesJSONnull | ✓ | SQLSQLite/nonasnull/models/nullability0diff |
| PKdefaultsFK | ✓ | 0diff/test96 DDLactual |
| Seedlegacy | ✓ | registry27/test234/249 SQLreal |
| ContractJSONWorkerJSON | ✓ | registry46/65 None/modelserializelegacy |
| legacyinstallsignature | ✓ | cpu493/668 fixedcolumnsourceonly |
| fullhistoricalguards | ✓ | SQLtriggersactualbodyunchanged |
| fix1fix2helpers | ✓ | fix1 23/78 fix2 39/56 test128 |
| authorityqueries | ✓ | cpu258/270/275 test2664futuretables |
| immutable0001..7 | ✓ | 217pins0diff historicalrevisions |
| acceptedcodecimmutable | ✓ | 50e1de3apinsstable |
| PORT01v1projection | ✓parcial | snap24/28 test145 SELECTreal |
| globalexclusions | ✓ | setting/provider/presetexact |
| populateddigests | ✓parcial | test195heads6/7 docdigestsafterrollback |
| reinstallrealeffects | ✓ | test195 schemascolumnsrowsvalues/invalidationbaseline |
| uninstallrollback | ✓ | test195 bothtransactionsreverted |
| TDDreplay | ✓ | REDfuturetrigger2fails04:29:43.825703Z |
| TDDprojection | ✓ | REDnoColumnSong.future_m2 04:29:50.727963Z |
| TDDhelpers | ✓ | RED4actualtriggerfuturecolumn |
| TDDauthorityqueries | ✓ | restoredoriginalselects RED4OperationalError04:43:12.193444Z before rewrite |
| REDincidentsseparate | ✓ | indent/type/assertpreliminarynotcredited |
| currentfocaltests | ✓ | 23PASSown5.78s |
| wholecoverage5 | ✓apoyo | cpu92.053/85.256/89.738;fix1 100;fix2 98.701/98/98.425;registry100;snap93.643/87.815/91.499 |
| noomitexclude | ✓ | sourcefilesystem/configfalse/excluded0 |
| suitefocalidentity | ✓ | 699cases698PASS1SKIP then23focal4testsaddedlater |
| constitutionbaseline | ✓ | C42 historicpinsimmutable |
| constitutionsongtake | ✓ | C21/22 noedit/publication |
| constitutionserverpaths | ✓ | C34/46 privateSQLite44imports |
| constitutionledgerclosure | ✓ | C72 taskopennoQAclaim |
| interopOpenAPI | n/a | nochangegeneratedschema/docs |
| knowledge | ✓ | ADR/db0hits directcontractread |
| T05personallibrarybackup | no verificable | personalWALbackuprestore realpending |
| T05CPUauthoritySQLv2 | no verificable | schemaORMv2 integratedpending |
| PORT01fullv2 | no verificable | newhead/mixed/crossfadehistorypending |
| CA16CA17CA29full | no verificable | spec171/172/184 operations/lineage/publicationfullpending |
| fullVerificationQA | no verificable | T05open QAactualtestSHA after4casespending |

EjecutadoA1: managedenv/.venv -B focalactual23PASS5.78s/217pinsbeforeafter/44imports privados;27M1tables356columns exacttypes/nullability/PK/serverdefaults/FKtarget/SQLtypes/codecmodels compared0diff. RED/cov/JUnitactor leídos y sourcefinalscope actual. Warningcache_dir por no:cacheprovider, sinfallofuncional. Fuenteprivatefixesdentro6owned; versiones0001..7 yacceptedcodecimmutable. Dactivated por4routesmigrations; Cfalse. No performanceverdictdesdeA, sin producto/generaciones/backupactualclaim.


## LenteB completa

| CriterioB | Estado | Evidencia |
|---|---|---|
| staticregistry | ✓ | registry85;356types+futuretablebeforereloadrealheads6/7 |
| columnstype/null/default/FK | ✓ | registry86/27tables356columnsbaselineexact |
| 3codecs | ✓ | registry26/45/65 AST methodsbaselineexact |
| seedNULLinvalid | ✓ | test230/23ownPASS/SQLaliasesSeedtyped |
| replayhistórico | ✓ | test77/privateSQLreal6/7 |
| CPUfixedguards | ✓ | cpu668/reinstallactualschemasallrowsequal |
| helpersdirty | ✓ | fix1 24/78 fix2 54;84/125DDLbyteexact |
| authorityselectsbounded | ✓ | cpu270/276/test266+43regressionownPASS |
| v1projection/excluded | ✓ | snap27/422/preimagefullpopulatedequal |
| digests/relationships/SQLRows | ✓ | snap84/121/434 aliasesmutationignored |
| privatefieldsNULL | ✓ | snap36/67 codecsbaseline |
| restorecollisionunboundedseed | ✓ | snap632 realroundtrip/unchangedcollision/seedtest |
| custodyimports | ✓ | 217pins44/48ownprivateimports |
| T05fullSQLv2APIpublicationlibrarybackup | no verificable | 2Afreezeonly nofutureintegrationproof |

## LenteD completa

| CriterioD | Estado | Evidencia |
|---|---|---|
| N+1introduced | ✓ | cpu2674grouped;24projectionSELECTidentical |
| libraryscale | ✓ | snap422/inmem30/100/1000songs20takes:25queriesbothmedian4.826–5.052ms |
| takebatchscale | ✓ | unchangedclosure_rows7;1000songs20980takesroot1000,baseline33frozen33queries31.920/31.581ms,batch400IDs |
| registryconstruction | ✓ | registry86/snap24 oneimport6.679msmedianstableidentity |
| SQLguardsworkperrow | ✓ | samegeneratorsCPU40sentences196836B/fix1 84/32890B/fix2 125/141386B |
| restore/serialization/locks | ✓readsource | snap69/496/582/673 nochangedloopslocks/collisionbatches400 |

Bincidentespropiosharnesssinuninstall/JSONadjacentespreimage corregidos sinfuentes, no productbugs niQA. Dlatencias soninmemory/sólo localcomparación, noIOdisco ni concurrenciaverdict; generadoresregistranSQLnoinstalación real. Baseline698PASS1skipWindowsoldtestSHAbefore4querytests+focalfinal23truthful. No fixtureactualpersonal-library/backup/generationclaims. NEWSQLv2/ORMv2API/Songv2/import/publicación/PORT01full/walbackupM1personalpending. NoT05/M2closure.
