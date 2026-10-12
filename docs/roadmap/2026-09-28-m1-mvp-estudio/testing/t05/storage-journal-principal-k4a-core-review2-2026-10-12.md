# K4a core — revisión2: dos Important nuevos

ROOT conserva el FULL30A/18B histórico inferior, sin reducir pendientes. A2 corrigió A01/A02 (37+35RED funcionales;23DTOguards+12counterborders); reprodujo78RED en preimágenes y268CPU propios,46pins estables. B2 confirmó escenarios originalesB01postTRUE yB02typedentry corregidos;268CPUpropios y46pinsestables. B03/B04 nuevos confirmados por ROOT funcionesCPUactuales, noSDK ni fakegrant.

FULL30A actual: cinco comunes y siete pares conservados con sus límites;18K4a conservados,01/03/07/08/10/14/18 mantienen pendientes completos. K4a04/05/07/16 conformidadTDD corregida. K4a11/12/15/18 conformidad de A queda acotada por B03/B04. FULL18B actual:01–10/13/14/16/17✓enalcance;08positivoK2no verificable;11✗B03/B04,12✗B03,15✗B03/B04,18✗B03y supervisorpendiente. Los siete pares mantienen cotas históricas/RSS/fullscopependientes. Whole80actualROOT sóloapoyo, noQA.

| ID | Grado | Estado/escenario actual | Evidencia |
|---|---|---|---|
| A01 | Important histórico | CorregidoR2 |37REDmonofocales/retiroguardwhole/rewrite/GREEN |
| A02 | Important histórico | CorregidoR2 |23guardsDTO+12counterborders35REDauténticos |
| B01 | Important histórico | Corregido escenario originalR2 |postTRUE output/frame/preimage/raw/error custody; ROOT2ownnativecuts |
| B02 | Important histórico | CorregidoR2 |IdentityErrorissue/bootstrap a entrada domain poisoned |
| B03 | Important nuevo |semantic_known no acredita cleanup terminado; mismo frame.semantic_rejection reissued antesClose deja stateLIVE/poisonFalse/open1/closes0/sibling22calls |identity611–616,707,711;ROOTprobeCPUexact |
| B04 | Important nuevo |ValueError/KeyboardInterruptantesClose pierde primariaPRINCIPAL_UNACCREDITED ycleanup: RESOURCE_UNKNOWN/cleanupNone aunquepoison/custodycorrectos |identity617–618/711–729,native1335→1377–1378;contract297/360;ROOT2CPUcuts |

0Critical/2Importantnuevos/0Minor. Scope2/0fuera/0avisos,C/Dauto false. Nuevos defects dentrocore, no pendientesK2 inventados. Fix2 exige REDfuncional causal de cadaescenario antescódigo. Rechazo conocido sólo se devuelve tras cleanup terminado/revocación real; interrupción antes/durante cleanup entraUNKNOWN, conserva primary primera con cleanupUNKNOWN y records/outputsinfree/retry/reset. Mismoobjeto no eximefaseactual/poison. CPU/native comparten regla, no fabricarAuthority/owner/pin. NativeFIX1a2eb/whole80noacreditaSHAfuture. Próxima review3FULL30A18B+6historygaps→QAindependienteantesCAS. T05/M1abiertos.

## FULL intento1 preservado como historial, supersedido por estados actuales superiores

# K4a-core revisión1 completa — fusión ROOT

ROOT normaliza30criteriosA(5comunes18K4a7pares)/18B;no transcripciónliteral. Basea81e035c/source85328c3b/IO6c1cb2e4/ABI85a93733 y3tests,6files2811diffline/46pins. N=ROOTnativefinal3scopepropio. AconformidadnormalacotadaB01custody/B02typederrorsnuevos; noyavistofullK4a/T05/M1.

| CriterioA | Resultado | Evidencia |
|---|---|---|
| tareas/verificación | ✓ T05abierto | tasks197/5317/CApendientes |
| scope6 | ✓ | tasks206/scope6fuera0avisos0 |
| Constitución | ✓ | C32BD/C41pesos/C43confinamiento/C65ledger/C73ADR |
| wholecoverage | ✓ apoyo sólo | ROOTfinal3same6SHA/85.8286/95.9315/93.2203lines branch81.9433/93.8023/91.4286 |
| interopE2E3OpenAPIstyle | n/a | 6PY |
| K4a01 | no verificable completo | identity161/abi288/gatesCPU,LinuxARM3232realpending |
| K4a02 | ✓ núcleo | identity161,1371/io169/latchreload/N |
| K4a03 | no verificable completo | identity182,906,952/test55,300,332,501;K2owner/pinsclosed |
| K4a04 | ✗TDD A01 | abi214,288/identity516,1081;RED05nofunctions |
| K4a05 | ✗TDD A01 | identity489/test173/REDdummycallbacks |
| K4a06 | ✓ núcleo | identity755/test28,48,445,466/RED06sid/65536 |
| K4a07 | ✗TDD A01/otrosbordespendientes | identity640,1315,1465/statsModifiedId/type/REDdummy |
| K4a08 | no verificable K2 legítimo | identity210–2265failclosed/noFakeCpuPin |
| K4a09 | ✓ núcleo | identity906,1452,1465/test385/policyepochs/N |
| K4a10 | no verificable full | K5reject0calls/N;K4bCREATEpending |
| K4a11 | ✗TDD A01/acotado B01 | identity402,561,991,1131;RED11A4runtime/primarycausalperoValueErrorlostoutput |
| K4a12 | ✓ núcleo/K2pending | io209/identity173,974/sharedpoisoncanonicalalias |
| K4a13 | ✓ núcleo/integraciónpending | io151,177,384/identity1371,1465,1525,1531/boundarybeforecontext,ownerK2heldfuture |
| K4a14 | no verificable exhaustivo | identity575,685,1217/io222,281/admissions4/2obs8192subcalls229376;9threads/pins/ownersborderspending |
| K4a15 | ✓normal/acotado B01unknown | identity1531/testio167/Nknowncloses;ValueErrorcutsnoexhaustive |
| K4a16 | ✗TDD A02/acotado B02 | identity259,282,297,332;DTOguardsbeforeredtype;KernelMemoryErrorleak |
| K4a17 | ✓ ownscope | ROOTmanager18768→launcher33100→real1548ready/run/reap/3obs66calls6closescharge0/SHA6same |
| K4a18 | no verificable completo | latchterminal/Nownreap/supervisorproductionpending |
| B01pair allocator | ✓ | testio167/n131584B512r132095/invalidL131328 |
| B01pair metadata | ✓núcleo | io222,281/testio148/Lntailtype;notK2pin |
| B01pair queryext | ✗TDD A01/partialfunctional | identity516/test466/65536pos65537negREDdummy |
| B01pair SIDtail | ✓ | test445/SID68lastbyte/beyondtailreject |
| B01pairoverflow | ✓K1scope | b4097/a4608/a+n=b+r136192/noallocatorreuse |
| B01paircharge | ✓normal/acotado B01 | K1Nknownoncefree/noidentityunknownexhaustive |
| B01pairpreimagesquotas | no verificable exhaustive/acotado B01 | test346,407,420/runtimecutretains;ValueErrorcutsdiscard/cotaRSSnotclaimed |

| CriterioB | Resultado | Evidencia |
|---|---|---|
| K4a01 | ✓ funcional scope | gatesbeforeloaderCPU |
| K4a02 | ✓ funcional scope | latchreloadIOconsumed |
| K4a03 | ✓ funcional scope | nominaltypesCPUsource/policy/epoch/callref |
| K4a04 | ✓ funcional scope | fakeSDKranges/layoutCPU |
| K4a05 | ✓ funcional scope | absenceFALSE1008NULL+negatives |
| K4a06 | ✓ funcional scope | SIDreturnlength/current65536 |
| K4a07 | ✓ funcional scope | beforeaftercurrentModifiedId/typeCPU |
| K4a08 | ✓ funcional scope | 5K2seamsfailclosed/notpositiveK2 |
| K4a09 | ✓ funcional scope | freshobs/admissions4/2scope |
| K4a10 | ✓ funcional scope | K5beforequery |
| K4a11 | ✗B01 | A4ValueErrorpostTRUEmaskedknown/outputlost |
| K4a12 | ✓ funcional scope | sharedK1poison/alias |
| K4a13 | ✓ funcional scope | boundarycontext/factorybarriersK2notactivated |
| K4a14 | ✓ funcional scope | quota/metadataL/n/B/r/tailCPU |
| K4a15 | ✗B01 | A4allowsdiscard/freebeforeownership |
| K4a16 | ✗B02 | K1poisonescapesKernelErrorallocate |
| K4a17 | ✓ funcional scope | NreadactualsameSHA3obs6closescharge0/reap |
| K4a18 | ✓ funcional scope | lifetimeCPUterminal/productionSupervisorpending |

| ID | Grado | Defecto/escenario | Estado |
|---|---|---|---|
| A01 | Important | identity489/516/640 guardas04/05/07/11sinREDcausal. red05-07-11UTC21:00:17 nueveDIDNOTRAISE porgetattrlambdaNone/funcionesausentes;callbacksNOalcanzados;green0521:01:28 implementófunciones/validacionescompletas. RED17ABIausente yotrosRED11no suplenesasguardas | confirmadoA/ROOTsourcepreimages; borrar/reescribirguardanueva trasREDmonofocalalcanzable |
| A02 | Important | identity259/282/297/332DTOvalidatorsantesREDrechazo. red16UTC21:02:12sólodictvsIdentityInfo;green14-1621:02:32cuatroDTOguards;red16-seamsdiagnosticfuture no valida esasguardas. testdiagnosticExactTypes sinREDdedicado | confirmadoA;guardsDTOcada criterio despuésREDno nombre/tiposausentes |
| B01 | Important | identity644/1319 capturaValueErrorgenéricacomo rechazo conocido. A4trasOpenProcessTokenTRUEanteshandleparse/register: principalcode→revoked,opened1close0frame0handles{};sentinel→unknownframe0. Nativecompartehelpercatch ybootstrap1435–1439puedefreebackingsinownership | confirmadoROOT2casosfuncionesCPUreales/sourcealiasCPU/no SDK; preimageNULLnohandleactual,retenerraw/poisonno free/retry |
| B02 | Important | identity1473 kernel_domain.__enter__poison posterior→KernelMemoryErrorOWNER_RETIRE_REQUIRED/allocateantesnative_live;callerIdentityErrornocaptura | confirmadoROOTASTrealcontrolflow/constructorKernelErrorreal,nograntniSDK; typedIdentityErrorissueantescalls |

0Critical/4Important/0Minor,sinrebate/deuda. Nativefinal3/whole80/164CPUverdaderossólo eseSHA, noQA/completion. Bpropio164PASS12deselected yCPUtraceA4/ASTcontrolflow,46pins6candidateshashstable;AlecturaASTrecibos(rawinitialquotingSyntaxErrorcorregidoscriptsinproductofault). Incidentesgreen13memorydirect/freeze2changedtestpreservados, no positivosautorizados. K2real noexiste y5futureseamsFAILCLOSED,no fakeowner/pin;K4b/K3/G1/K5fullchain/storeACKrecovery/ext4bootstraplifecycle/supervisor/E2E/manuales aúnpendientes.

FIX1freshpreserva18/7/fullT05scope: A01/A02borrar lógicaNUEVAguardacompletaconpredicadoyreescribirtrasRED funcionalmonofocalreal sin getattrdummy/importfallidos/nombresclaseantesguarda. Lógicaheredada yREDsrealmenteauténticosconservar. B01separarrechazosemánticoplenamentereconocido decualquierinterrupcióntipoValueErrorpostTRUEpor fase/custodiareal,noclassificationporstrinCODES. Unknown conservaoutput/framepreimage/record,errorprivado;no clear/close/retry/free nihealthy/siblingdomain;bootstrapquarantine/nocleanupfingido. B02adaptarentradaKernelDomainfailantecallererrorIdentitytypedcode/opissue,sinsilenciar/resetpoison. CallbackdoublesCPU separado,noNativeauthorityfabricada; nativeharnesspropioporROOTsólotrasfreeze/auditcutnuevo. 2026-10-11T22:17:27.280236+00:00
