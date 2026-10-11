# T-05/U2b1 — revisión de dos lentes, intento 1

ROOT fusiona A+B+C a 2026-10-11T09:20:39.783534+00:00: **0Critical,4Important,0Minor; candidato rechazado para adopción, FIX1 obligatorio**. D no aplica: auto y overlayrequiredC ambos Dfalse,0avisos. Canonicaldevauto intacto. Scopecheckexit0dosfiles0excludeduser. Ningún rebate o deuda aceptada.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Cleanup sin primaria implementado sin RED/test; runtime:558 | T05/U2b1 | pendiente FIX1: borrar sólo __exit__nuevo a stub→RED válido→reescribir; no restaurar cuerpo anterior | LenteA100runs/coverage558missing/probepropioexit0; defecto disciplina,no bug funcional |
| B01 | Important | KeyboardInterrupt posPENDING/pre reconocer libera arena, no poison; runtime:486 | T05/U2b1 | pendiente FIX1: ampliar custodia/cobertura transición, REDregresión previo | Bdouble5hijos;ROOTsinglefault/control6hijosreaped:arenadead/nextoptrue vscontrolalive/false |
| B02 | Important | KeyboardInterrupt posCloseHandle/pre publish permite retry con None; runtime:534 | T05/U2b1 | pendiente FIX1: estado idempotente reservado antes, REDregresión previo | ROOT[202,None] vscontrol[202],actualfakeNonefalse/retention |
| B03 | Important | KeyboardInterrupt posSUCCESS/pre registrar pierde adquisición; runtime:621 | T05/U2b1 | pendiente FIX1: arena/owner durante transfer, REDregresión previo | ROOTopen1/closed[]/owner0/retainedfalse vscontrolclose202 |


ROOT verificó freeze1242payload/5reparsestat-only,22inputs,100runs54RED46GREEN,112actorPASS,ASTpreservado18/31 ywholelíneas93,2692%/ramas89,3258%/combinado92,2636%sinexclusiones. Green actor no invalida gaps. Csinseguridad introducida; sus✓lifetime son limitados a nodos previstos, no aprueban ventanasB01-B03. A no verificó esas ventanas directamente, ROOT/Bsíconcontrols. Ningún cumplimientoT05/M1 amplio ni QAindependiente aún. Reviews47PASSdeB yC se solapan y **no se suman**, A17controlesdirectos también. Reproductores sólo dobles ownprocesos reaped, noPENDINGnativo ni garantías frentea interrupcionesrepetidasdelhandler. No writesdeproducto/Gitshared/admin/WSL/ACL/data.

Módulo actor1556847e29c4e5ba08486765ededaf80110b7851a715ad83bfd415dd76dc5c29/tests11e598146a73ded9bb144c113baa0e75a379379c8473b2d408204c390e662093 permanece privado. CanonU2a91e279/6671db intacto. ROOTcorroboración causal independiente: .cache/dev-cycle/m1/storage-nt-observation-u2b1-review1-20261011/reproduce_b_root.py yroot-b-reproduction/receipt.json (6childexit0,reaped). EntregaB5childterminateExit1 diferenciada en lens-b-reported-reproduction.md. Scripts/streams/JUnit/coverage originales conservados. Tokens/eur/horasIA realesnull.

## Tablas completas recibidas


# Lente A · intento 1

Diff901701760860b52488cd166556652c6f3cd6a518…HEAD ∪ sincomitear, dosficheros/1231líneas añadidas, completo leído por partes. Rutas relativas snapshot revisión. E=.cache/dev-cycle/m1/storage-nt-observation-u2b1-20261011/.

| Criterio (T-XX / objetivo) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| T-05/U2b1: alcance exclusivo apertura existente, metadata y cierre | ✓ | scripts/storage_journal_windows.py:562; FILE_OPEN fijo, sin create/store/ACK/geometría/lifecycle. release-root.md:13–18. |
| Archivos declarados y preservación U2a | ✓ | tasks.md:208; Git privado sólo dosfiles. Independiente18defs runtime/31testshelpers originales exactos. ScopeROOT2files0fuera/avisos/exclusuario. |
| Inputs: UTF16, componente único, nombres reservados, parent/kind cerrados | ✓ | scripts/storage_journal_windows.py:437,:562; tests/test_storage_journal_windows.py:714,:885,:1432. Dobles independientes. |
| ABI x64 y perfiles access/share/options | ✓ | scripts/storage_journal_windows.py:585,:759,:865; tests:848. ABI/perfiles ejecutados; E/primary-sources.json fuentes oficiales. |
| NT return gobierna; error no adquiere sentinel; FILE_OPENED obligatorio | ✓ | scripts/storage_journal_windows.py:619; tests:904,:913,:922 independientes. |
| Metadata mismohandle, copia frozen, metadata adversa | ✓ | scripts/storage_journal_windows.py:640,:699,:815; tests:930,:969,:978. JUnit/doblesleídos;copia/BOOLerror ejecutados. |
| Ordinary/missing identidad/path/SD y prestado conservados | ✓ | tests:1228;evidencianativa yJUnit112leídos;ausencia no crea. |
| Junction nueva sin traversal; hardlink/tipo rechazados | ✓ | tests:1312,:1324;E/native-junction-witness.jsonIDsalias/targetdistintos,pre/postexactos,sentinelintacto. |
| Sharing bilateral y directory rename/delete | ✓ | tests:1264,:1293;controleskernel/bothordersleídospruebas/JUnitfrozen. |
| Pending/entered arenas/owners/poison global contingencias previstas | ✓ | scripts/storage_journal_windows.py:471;tests:1072,:1365;witness/hijosreapleídos. Dobles, noPENDINGnativo. |
| Ventanas de interrupción posretorno | no verificable aquí | ROOTcomunicaB pendientes scripts/storage_journal_windows.py:486/adquisiciónSUCCESS; no reproducidos/aprobados porA, fusionar B. |
| Close revocación/closeonce/causas/serialización | ✓ | scripts/storage_journal_windows.py:513;tests:986,:1004,:1108,:1140,:1443;doblesdirectosejecutados,native151→170→171→172→171→170/+19honesto. |
| TDD causal cleanup corregido yRED46 | ✓ | Hashes/JUnit100:54RED46GREEN. close01..08REDadquisiciónválida-close/contextstubsuperseden8rojosinsuficientes. RED46close():returnNoneantesrewrite. |
| TDD causal todas ramas nuevas cleanup | ✗ | A01scripts/storage_journal_windows.py:558 implementadasintest/REDsinprimaria. |
| Regresión/cobertura/Ruff | ✓ | E/final-validation112PASS0FAIL/ERROR/SKIP;485/520lines93,2692%,159/178branches89,3258%,combinado92,2636%,ex0,Ruff0;actor,noQAindependiente. |
| Constitución/O2/S1/contratosgenerados | ✓ | Constitución32/43/65sinBD/almacenamientoexterno/cierretareas; noAPIcontratos,interopn/a(commands/agents/hooksintactos). |
| CierreT05/M1/verificacionesamplias | ✓ | tasks202/214/4822abierta;3CAamplios/worker/manifiestopersistentespendientes; LinuxQAposterior. |

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| A01 | Important | Rama nueva cleanup sintest/REDcausal, release-root.md:28/tasks.md:4828 | T05/U2b1 | scripts/storage_journal_windows.py:558 | withchild termina normalmente yCloseHandleFALSE ⇒ NativeObservationError. Cuerpoexistía pairs02-green; close05/06REDdirectclose,close07REDValueErrorprimary;46nodesnoescenariosinprimaria. Coverage558/branch555→558ausentes. | — |

Ejecutado: envgestionadoROOT;hashes/preimágenes/JUnit100,pins20readonly,AST18/31,17controlesdirectosPASSABI/inputs/status/close/concurrencia,finLIVE_CONTEXTS0/RETAINEDNone. ProbepropioaisladoA01NativeObservationError/closeonce/retainedconfirmados,exit0/hijoreaped. Primerproberojoassertlocalizadaarnésconservado/sóloassertcorregido. A01faltaTDD,no bugfuncional. Noejecutadosuite nativafrozen/LinuxDocker/gatesamplios. Ningún writecanon/ledger/Git/GPU/services/ACLexisting. ConsultamemoriatécnicasinaciertosADR. VentanasROOTcomunicadasnofusionadascomogapA.


# Lente B · intento 1

Diff901701760860b52488cd166556652c6f3cd6a518…HEAD ∪ cambios sincomitear,2files1231addedlines,diffcompleto leído/personabackend aplicada. 3Important0Critical0Minor.

| Criterio (T-05/U2b1) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Inputs cerrados y ABI x64 | ✓ | scripts/storage_journal_windows.py:437,759,872; pruebas componentes/tipos/ABI/perfiles pasan. |
| NTreturn gobierna/errornosentinel/FILE_OPENED | ✓ | scripts/storage_journal_windows.py:619,626; pruebas status/IOSBdistinto/Informationinválida pasan. |
| Metadatahandle/copiafrozen/rechazoadversa | ✓ | scripts/storage_journal_windows.py:640,697,713;BOOLerrors/attrs/links/sizes/path pasan. |
| Aperturaexisting/sharingbilateral/objetosnativosown | ✓ | tests/test_storage_journal_windows.py:1228,1264,1293,1312,1324;Windowsnativopasan. |
| Serializaciónqueryclose/contextosindependientes | ✓ | tests:1140,1387ambas pasan. |
| Pending/exceptiondentrocallbackretainowners/arena/blocked | ✓ | tests:1072,1365;controlB01arenaalive/nextopblocked. |
| TransiciónretornoPENDING→reconocimiento/retención | ✗ | scripts/storage_journal_windows.py:486B01arena dead/nextopallowed. |
| TransiciónSUCCESSopen→acquisitionregistered | ✗ | scripts/storage_journal_windows.py:621B03pierdeadquisición sin registrar/cerrar. |
| Cierreordinario/exceptiondentrocallback | ✓ | tests:986,1108,1443;controlB02closeonce. |
| Transiciónretornoclose→publicaciónidempotente | ✗ | scripts/storage_journal_windows.py:534,546B02observaciónmissing/retryCloseNone. |

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| B01 | Important | Interrupción posretornoPENDING sin retention/poison | T05/U2b1 | scripts/storage_journal_windows.py:486 | Una KeyboardInterrupt posSTATUS_PENDING/pre reconocimiento fuera try:retainedfalse/arenaalivefalse/nextoptrue vscontroltrue/true/false. | — |
| B02 | Important | Interrupción posclose deja idempotencia incompleta | T05/U2b1 | scripts/storage_journal_windows.py:534 | Una KeyboardInterrupt posCloseHandleSUCCESS/pre_close_observation:handleNone/obsmissing,retryClose(None),[202,null]/unknown/poison vscontrol[202]/closed/noPoison. | — |
| B03 | Important | Interrupción preadopciónhandleSUCCESSpierdeownership | T05/U2b1 | scripts/storage_journal_windows.py:621 | Una KeyboardInterrupt posSTATUS_SUCCESS/preObservedHandle:opens1/closed[]/owned0/retainedfalse y siguienteopenentra. | — |

Ejecución manageduvpytest owncapsula reviewer-u2b1-b1-20261011/snapshot/tests/test_storage_journal_windows.py -q -k observation:47PASS65deselectedexit0(46new+1U2a),JUnitobservation.xml. Repro exactoentregadoROOT B01/B02/B03+controls5ownchildren,parent0,stderrvacío,terminados/reaped; lens-b-reported-reproduction.md entrega exacta preservada. ROOTcorrobora independiente3faults+3controls/6ownchildsexit0/reaped;root-b-reproduction/receipt.jsonleído porB. FuentesSHAfinal1556847e/11e598exactascapsulaROOT.

Sólo una interrupción durante cada transición, no resistencia a interrupciones repetidas handler ni PENDINGnativo. Sinmemoriatécnicadocs/knowledge snapshot. TDD/cobertura/admisión durableotraspuertas; T05/M1noacreditados.


# Lente C · intento 1

Diff base `901701760860b52488cd166556652c6f3cd6a518` + cambios sin comitear (2 ficheros). Sin hallazgos de seguridad introducidos o reabiertos. Contexto fresco, diff completo leído por bloques de runtime y tests. C requerida mediante overlay privado; configuración canónica auto intacta. Referencias: vulnerability-taxonomy.md, language-patterns/python.md y false-positive-suppression.md plugin1.21.1.

| Criterio (T-05/U2b1) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| UTF16, componente único, traversal, ADS y dispositivos | ✓ | scripts/storage_journal_windows.py:437; tests de componentes e inputs pasan, incluidos separators, NUL, dot/dotdot, ADS, namespaces y nombres reservados. |
| Parent vivo y apertura relativa sin autoridad por scalar | ✓ | scripts/storage_journal_windows.py:491,:562; tipo privado exacto, owner/context retenidos, metadata del parent consultada antes de NtCreateFile. Contrato exige owner cooperante. |
| No creación, escritura ni ampliación arbitraria de permisos | ✓ | scripts/storage_journal_windows.py:585; perfiles fijos de access/share/options y FILE_OPEN. Test nativo acredita ausencia sin creación. |
| Reparse, hardlinks, dispositivos y metadata adversa | ✓ | scripts/storage_journal_windows.py:640,:694,:841; negativos causales pasan; hardlink/tipo y junction nueva rechazados nativamente, sentinel conservado. |
| Exclusión bilateral de WRITE/DELETE y custodia del directorio | ✓ | tests/test_storage_journal_windows.py:1264,:1293 → PASS nativo ambos órdenes, dos observers compatibles y rename/delete bloqueados durante retención. |
| Retorno NT/BOOL antes de interpretar salida | ✓ | scripts/storage_journal_windows.py:618,:671; NT error no consulta/cierra sentinel, Information incorrecto cierra adquisición propia y BOOL falso no acepta buffer plausible. |
| Lifetime, poison global y cierre sin retry | ✓ | scripts/storage_journal_windows.py:458,:506; ocho dobles en hijos propios acreditan retención, bloqueo entre contextos y close unknown; ocho reaped y cero PIDs vivos. |
| Metadata sin HANDLE ni capacidad operativa | ✓ | scripts/storage_journal_windows.py:815; observación frozen con copias/raw, sin HANDLE; no store, writer, bootstrap, ACK o admisión de cadena añadidos. |
| Inyección, secretos, deserialización, SSRF y exposición nueva | ✓ | Ambas fuentes completas leídas. Subprocess nuevos pertenecen al harness y usan cuerpos/nombres propios; no entrada externa hacia código, shell, SQL o red. |
| Rechazo de plataforma sin cargar DLL | ✓ | scripts/storage_journal_windows.py:856; test_observation_nonwindows_without_dll PASS. Simulación de plataforma, no ejecución Linux. |

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| — | — | Sin hallazgos | T-05/U2b1 | — | — | — |

Ejecución propia uv managed pytest cápsula reviewer-u2b1-c1-20261011/snapshot/tests/test_storage_journal_windows.py -k observation -q -p no:cacheprovider --basetemp=namespace/pytest-temp --junitxml=namespace/junit-c.xml. Exit0:47PASS65deselected0FAIL/ERROR/SKIP (46new+1U2a matching). Aviso Unknown config option cache_dir por desactivar cacheprovider. JUnit,8recibosreap,testigosnativos namespacepropio. SHAposteriores1556847e29c4e5ba08486765ededaf80110b7851a715ad83bfd415dd76dc5c29/11e598146a73ded9bb144c113baa0e75a379379c8473b2d408204c390e662093. Sin incidencias adicionales para enrutar. No acredita fullchainS1/PENDINGnativo/geometría/durabilidad/T05/M1.

Nota ROOT posterior a entrega C: B identifica ventanas de interrupción fuera de try que no cubren esos47nodos. Los ✓ originales de C se conservan como evidencia de su alcance, no como garantía global; B01/B02 se fusionarán como gaps de corrección y bloquearán aceptación.
