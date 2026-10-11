# T-05/U2b1 — revisión de dos lentes, intento 2

ROOT fusiona A+B+C a 2026-10-11T09:46:46.890459+00:00: **0 Critical,0 Important,0 Minor pendientes**. Los cuatro Important del intento1 están corregidos, sin rebates ni deuda aceptada. D no aplica según auto y overlay requerido, ambos false/sin avisos. La revisión permite QA independiente de la unidad; no incorpora código ni cierra T05/M1.

| # | Grado inicial | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Cleanup sin primaria escrito sin RED | T05/U2b1 | corregido: __exit__ borrado a pass, RED causal válido, reescritura distinta anterior | A2 verifica source-before/UTC/hash/JUnit; escenario propio PASS |
| B01 | Important | PosPENDING liberaba arena y dejaba operar | T05/U2b1 | corregido: custodia y poison cubren transición posretorno | B2/C2/A2 fault/control, arena/owner vivos, cero close/segunda operación |
| B02 | Important | Posclose permitía retry CloseHandle(None) | T05/U2b1 | corregido: reserva idempotencia/revocación/retención de unknown | Fault/control [202] una vez, sin None; 8close transiciones adicionales |
| B03 | Important | SUCCESS antes de registro perdía adquisición | T05/U2b1 | corregido: arena/owner durante transferencia y constructor | Fault/control custodia/no nueva operación;11open transiciones adicionales |


ROOT verifica588payloads FIX1 y1reparse stat-only sin traversal,23entradas snapshot/2targets modificados autorizados,6pares RED→GREEN con JUnit/streams/preimágenes/UTC,139actorPASS,18runtime/31testsU2a y60defs test/helpers U2b1 exactos. Whole oficial511/535líneas95,5140%,167/182ramas91,7582%,combinado94,5607%,0exclusiones/omit vacío/pragmas0; Ruff0. Diecinueve ventanas adyacentes son vecinosGREEN, no19RED. Dos regresiones durante el fix tienen pares causales propios, conservados. Primer intentoB02 era controlPASS fuera ventana; no acreditaRED. Primer probe recursos falló en harness y no conservó streams/counters; fuente y diagnóstico guardados y limitación explícita, segundo probe actual autenticado.

Resultados de revisión independientes A32/B59/C74 se solapan: unión exacta **74nodos**, no165, ni sumar actor139. ROOT verifica JUnit0FAIL/ERROR/SKIP, hashes de las cápsulas y27recibos nuevos exit0/reaped por revisor; anteriores4/8/8recibos tienen exit1 intencional terminate, no pytestFAIL ni exit0. Recursos nativos131cold→150import→151fixture→159preflight→160open/159close×12→158ownerclose; +19 y+8 no restados. Launcher5968wait0/runtime12156self-reported, ambos postwait no vivos; no wait independiente del runtime ni ausencia global fugas.

Runtimeaf192c76519d88e8b1cbd267a8326bf74e54a871dbcd5c0dc5a13a8297e56db4/testsf36ada14128344840267aa87df13f5d7383d0bc1d3da8345be608c5b02d4ef7a todavía privados. CanonU2a91e279/6671db intacto. Owner cooperante e interrupción única, noPENDINGnativo ni resistencia a handler repetidamente interrumpido. QA Linux/Windows actual y CAS siguen pendientes, así como geometría/bootstrap/store/writer/ACK/fullchain/ext4/lifecycle/E2E/manuales/Git. Jira desactivado; ningún mensaje externo. Tokens/eur/horasIA reales null.

## Tablas completas recibidas


# Lente A · intento 2

Diff `1c2ccb83b38af56e7f517a4e2530f0e5ccd7cdf7…HEAD` unido a cambios sin comitear: dos ficheros,1543líneas añadidas. Sin gaps pendientes de conformidad:0Critical/Important/Minor, A01 corregido. Diff completo leído por bloques; aprobados del intento1 conservados, correcciones/regresiones reevaluadas. F=storage-nt-observation-u2b1-fix1-20261011;R=reviewer-u2b1-a2-20261011 bajo .cache/dev-cycle/m1. Rutas código relativas snapshot.

| Criterio (T-05/U2b1) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Apertura existente, metadata y cierre exclusivamente | ✓ | scripts/storage_journal_windows.py:575; FILE_OPEN/perfiles fijos; releases excluyen geometría/create/store/ACK/bootstrap/fullchain/lifecycle. |
| Archivos declarados y preservación U2a | ✓ | tasks.md:208; sólo dosfiles Gitprivado. Independiente18runtime/31testshelpers exactos U2a; canon91e279/6671db. ScopeROOT0sinavisos/exclusuario. |
| InputsUTF16/componente/reserved/types | ✓ | Veredicto previo conservado; _validate_component y tests exactos preimagenFIX1. |
| ABI x64/perfilesaccess-share-options | ✓ | Previo conservado; _ObservationApi/estructuras/testABI exactos. |
| NTreturn/errornosentinel/FILE_OPENED | ✓ | scripts/storage_journal_windows.py:635; tests originales exactos; custodia no convierte outslotNTerror en adquisición. |
| Metadatahandle/copiafrozen/rechazoadversa | ✓ | Previo conservado; read_handle_metadata/MetadataObservation/tests exactos. |
| Ordinary/missing ID/path/SD/borrowedparent | ✓ | Tests nativos originales exactos; actorwhole139leído0fail/error/skip, no repetición nativa propia. |
| Junctionnotraversal/hardlink/type | ✓ | Previo conservado; fixtures/tests exactos; no reparsefrozen reutilizado/traversado. |
| Sharingbilateral/dirrename-delete | ✓ | Tests originales exactos y actorwhole actualverde; ningún nuevo writerclaim. |
| Pending/entered arena/owner/poison | ✓ | scripts/storage_journal_windows.py:476; B01/typedentered propios, arena/owner vivos/otroctxblocked; dobles,noPENDINGnativo. |
| B01 posPENDING/pre reconocimiento | ✓ | scripts/storage_journal_windows.py:481;tests:1595fault/control, una inyección, retenida/cero closes/segundaopblocked. |
| B02 posCloseHandle/pre publish | ✓ | scripts/storage_journal_windows.py:525,:532;tests:1600fault/control,[202]/noNone/unknown/retention. |
| B03 SUCCESS/pre registro | ✓ | scripts/storage_journal_windows.py:637,:640;tests:1605faultretainsarena/owner/poison/noClose/control[202]once. |
| Close revocación/closeonce/primary-cleanup/serial | ✓ | scripts/storage_journal_windows.py:514;propiosprimaryKeyboardInterrupt/3unknown/beforecall; anterioresconcurrenciaexactos. |
| A01 borrar __exit__, RED y rewrite | ✓ | F/actor-runs/a01-red/before-storage_journal_windows.py __exit__:pass. RED09:26:03.999–09:26:04.806UTCexit1/adquisiciónválida/withchildpass/falloCleanup no acreditado sin primaria debe generar error tipado. GREEN09:26:22.931–09:26:23.627exit0. Final:565distinto anterior,no restauración textual; prueba actualpropiaPASS. |
| TDD causal B01/B02/B03 | ✓ | Preimages/streams/JUnit6paresverificados. B01RED09:26:23→GREEN09:26:56;B02correctedRED09:26:40→GREEN09:27:20;B03RED09:26:26→GREEN09:28:05. RED1causacontractual/GREEN0. |
| Regresiones typedentered/closebeforecall | ✓ | RED/GREENauth typed09:28:36→09:28:37/beforecall09:28:06→09:28:14; testfunctions ASTigualRED/GREEN; propiasverdes. |
| 19 ventanas adyacentes | ✓ | tests:1671/19propioscadauno1inyección/arenaownerretained/blocked; vecinosGREEN,no19RED. |
| Regresión whole/cobertura/Ruff | ✓ | actor139PASS0fail/error/skip/deselection;511/535lines95,5140%;167/182branches91,7582%;combinado94,5607%;ex0,Ruffcheck/format0. Whole,noporcentajediffinventado. |
| Recursosnativos/límiteshonestos | ✓ | F/actor-native-resource-witness.jsoncold131→150import→151fixture→159preflight→160open/159close×12→158ownerclose;+19/+8conservados;primero inválidoexplicitado;launcher5968wait0/runtime12156ylauncherpostnovivos,noruntimewaitindependiente/nofugasglobalclaim. |
| Constitución/O2/S1/generatedcontracts | ✓ | Constitución18/25/33/35/37sinBD/externalstorage/cierretareas/cambiocontrato;ADR0075/76yreleasealcance;interopn/a commands/agents/hooks intactos. |
| CierreT05/M1 y ampliasverificaciones | ✓ | tasks202/210/214T05enprogreso/CAabiertos; no sustituyeworker/manifiestopersistente/LinuxQA/E2E/manual/M1acceptance;ninguna tarea cerrada sinverificación. |

| # | Grado | Gap | Tarea | fichero:línea | Escenario | CWE |
|---|---|---|---|---|---|---|
| — | — | Sin gaps pendientes A | T05/U2b1 | — | — | — |

Ejecutado entorno ROOT scripts/env.ps1 y uv frozen/no-sync/all-packages python -X utf8 -B -m pytest R/snapshot/tests/test_storage_journal_windows.py -q -k 'fix1 or context_preserves_baseexception_and_cleanup or unknown_close_retains_without_retry_child or close_beforecall_fault_is_unknown_child' con temporales/caché/JUnit propios:32PASS107deselectedexit0/6,50s, R/junit-a.xml.27FIX1+5regresiones anteriores, no sumaractor139. Lecturaindependiente6pares hashes/REDcausa/UTC/testASTigual,18/31U2a y60originales U2b1 exactos.27hijosFIX1exit0/reaped+4reciboscontingenciasprevias. Fuentesfinalesaf192c76519d88e8b1cbd267a8326bf74e54a871dbcd5c0dc5a13a8297e56db4/f36ada14128344840267aa87df13f5d7383d0bc1d3da8345be608c5b02d4ef7a.

Noejecutadowholepropio/native resources/DockerLinux/gatesamplios. Snapshot sin docs/knowledge;ADRleídosdirecto,sinmemoriacurada. Dos scriptslecturafallaronquoting/rutapreimagen, corregidos sin crédito producto. Veredictos B/C pertenecen respectivaslentes; A acredita release/TDD/escenarios, noadopciónM1.


# Lente B · intento 2

Diff `1c2ccb83b38af56e7f517a4e2530f0e5ccd7cdf7…HEAD` unido a cambios sin comitear, dos ficheros. Diff completo leído por bloques; persona backend. Sin defectos: B01, B02 y B03 corregidos.

| Criterio (T-05/U2b1) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Inputs cerrados y ABI x64 | ✓ conservado | Veredicto intento1; inputs vecinos ejecutados, sin regresión. |
| NT return gobierna; error no adquiere sentinel; FILE_OPENED | ✓ | scripts/storage_journal_windows.py:635; status/error/IOSB/Information pasan. |
| Metadata por handle, copia frozen y rechazo adverso | ✓ conservado | scripts/storage_journal_windows.py:661; negativos vecinos pasan. |
| Apertura existente y sharing bilateral nativo | ✓ conservado | Evidencia aprobada intento1, no repetida ni reabierta. |
| Serialización query/close y contextos independientes | ✓ | Dos tests concurrentes pasan en junit-neighbors-b2.xml. |
| Pending/entered conservan arena/owners/bloqueo | ✓ | scripts/storage_journal_windows.py:470; contingencias y múltiples owners pasan en hijos propios. |
| B01 retorno PENDING→reconocimiento | ✓ corregido | scripts/storage_journal_windows.py:481; fault/control retienen arena/owner y bloquean ambos contextos. |
| B02 retorno CloseHandle→publicación idempotente | ✓ corregido | scripts/storage_journal_windows.py:525; fault/control closes[202], nunca None; fault unknown retenido. |
| B03 SUCCESS→registro adquisición | ✓ corregido | scripts/storage_journal_windows.py:617; fault retiene adquisición/arena/owner sin close/nueva operación; control closeonce. |
| Constructor, Information, metadata y retorno apertura | ✓ | scripts/storage_journal_windows.py:508; once transiciones adyacentes con interrupción única pasan. |
| Reserva/revocación, native, publicación, retirada y retorno close | ✓ | scripts/storage_journal_windows.py:523; ocho transiciones conservan unknown/owners/contexto, sin retry. |
| Excepción tipada durante llamada entered | ✓ | scripts/storage_journal_windows.py:484; test_fix1_entered_typed_exception_still_retains pasa. |
| Contexto: primaria preservada y cleanup unknown sin primaria tipado | ✓ | scripts/storage_journal_windows.py:565; con/sin primaria pasan, closeonce y retención. |

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| — | — | Sin defectos | T05/U2b1 | — | — | — |

Ejecutado con entorno ROOT, uv frozen/no-sync/all-packages y pytest en cápsula reviewer-u2b1-b2-20261011/snapshot: FIX1 27PASS exit0; vecinos32PASS exit0. JUnit disjuntos59casos únicos, cero fail/error/skip. junit-fix1-b2.xml y junit-neighbors-b2.xml;27recibosFIX1 exit0/reaped,8vecinos terminateintencional exit1/reaped, ningún PID observado vivo. SHA posteriores af192c76519d88e8b1cbd267a8326bf74e54a871dbcd5c0dc5a13a8297e56db4/f36ada14128344840267aa87df13f5d7383d0bc1d3da8345be608c5b02d4ef7a. Aviso cache_dir por no:cacheprovider. Sin memoria docs/knowledge en snapshot.

TDD A01, cobertura y QA son otras puertas. Sólo una interrupción; no acredita PENDING nativo, interrupciones repetidas del handler, caller hostil, fullchain o T05/M1.


# Lente C · intento 2

Diff `1c2ccb83b38af56e7f517a4e2530f0e5ccd7cdf7…HEAD` unido a cambios sin comitear, dos ficheros. Sin hallazgos de seguridad introducidos o reabiertos: 0Critical/Important/Minor. Diff completo leído por bloques; comparación original→FIX1. Reevaluados cambios y conservados veredictos anteriores. C requerida overlay privado; dev canónico intacto. Criterio propio conforme prompt literal, no auditoría global.

| Criterio | ✓/✗/no verificable | Evidencia relativa snapshot |
|---|---|---|
| Custodia posPENDING y excepción entered | ✓ | scripts/storage_journal_windows.py:476; B01 fault/control y excepción tipada: arena/owner retenidos, poison global, cero close y segunda operación bloqueada. |
| Custodia SUCCESS→registro wrapper | ✓ | scripts/storage_journal_windows.py:618; B03 fault línea637 conserva arena/output/owner y bloquea usos; control closes[202] una vez. |
| Cierre sin retry ni autoridad residual | ✓ | scripts/storage_journal_windows.py:525; B02 fault unknown/_handleNone/closes[202]; repetición no CloseHandle(None). |
| Retención durante desregistro/publicación | ✓ | scripts/storage_journal_windows.py:543;19faults adyacentes exactamente una inyección: arenas vivas, poison, owners recuperados al cerrar, sin segundo syscall. |
| Cleanup contexto conserva frontera autoridad | ✓ | scripts/storage_journal_windows.py:565; sin primaria error tipado/unknown/retención/closeonce; primaria original pasa. TDD corresponde A. |
| Parent prestado, componentes, apertura relativa | ✓ | scripts/storage_journal_windows.py:491,:575; wrapper privado exacto, owner cooperante vivo, metadata previa, componente cerrado; scalar/traversal/ADS/devices/kind pasan. |
| Perfiles acceso/operación existing | ✓ | scripts/storage_journal_windows.py:605; access/share/options fijos/FILE_OPEN; ABI y nativeausencia sin create pasan. |
| Retorno NT/BOOL y metadata adversa | ✓ | scripts/storage_journal_windows.py:635,:661; NTerror no adquiere/cierra sentinel; reparse/hardlinks/device/type/path/sizes/BOOLfalse rechazan. |
| Sharing/junction nativos conservados | ✓ | tests/test_storage_journal_windows.py:1264,:1293,:1324; ambos órdenes WRITE/DELETE incompatibles, rename bloqueado, junction nueva rechazada/sentinel intacto. |
| Metadata sin capacidad/canales peligrosos nuevos | ✓ | scripts/storage_journal_windows.py:836; copia frozen sin HANDLE; no writer/create/ACK/bootstrap/entradaexterna shell/código/SQL/deserialización/red. FIX1 subprocess intérprete/scripts propios. |

| # | Grado | Gap | Tarea | fichero:línea | Escenario | CWE |
|---|---|---|---|---|---|---|
| — | — | Sin hallazgos | T05/U2b1 | — | — | — |

Ejecutado entorno ROOT/uv managed pytest cápsula reviewer-u2b1-c2-20261011/snapshot/tests/test_storage_journal_windows.py -q -k "observation or fix1" -p no:cacheprovider con basetemp propio/JUnitjunit-c2.xml. Exit0:74PASS65deselected/1warning cache_dir/7,17s; JUnit74/0fail/error/skip.27FIX1child receipts exit0/reaped/stderr vacío y8anteriores reaped; raw B01/B02/B03 y19faults cotejados, nativeordinary/junction propios. Fuentes posteriores exactas af192c76519d88e8b1cbd267a8326bf74e54a871dbcd5c0dc5a13a8297e56db4/f36ada14128344840267aa87df13f5d7383d0bc1d3da8345be608c5b02d4ef7a.

No incidencias adicionales. Owner cooperante/interrupción única; no PENDING nativo, handler repetidamente interrumpido, ausencia global fugas, fullchain S1/geometría/durabilidad/T05/M1/QA integral. No writes canon/ledger/Git/frozen/ACL existentes/services.
