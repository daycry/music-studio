---
design: storage-journal-principal-k4a
titulo: Principal efectivo, emisor privado y admisión previa del journal Windows
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: ../2026-09-28-m1-mvp-estudio/spec.md
evaluacion: n/a
plan: ../2026-09-28-m1-mvp-estudio/improvement-plan.md
adr: n/a
opcion_elegida: O1
recomendada: O1
pasada: 2
validada_por: ROOT bajo delegación vigente del propietario
validada_en: 2026-10-11T19:45:58.478501+00:00
revision: pendiente
qa: pendiente
adopcion_canonica: pendiente
implementacion: no liberada
correccion_documental: FIX1 B01; arena K1 alineada sin ampliar el workspace SDK
generacion:
  fuente: estimado
  tokens_reales: null
  euros_reales: null
  horas_ia_reales: null
  medidor: no ejecutado por alcance de ROOT
---

# Diseño — Principal y admisión previa K4a

> Spec [aprobada](../2026-09-28-m1-mvp-estudio/spec.md). Contrato consumidor [K2 §4.2](../2026-09-28-m1-mvp-estudio/storage-journal-acquisition-design.md). O1 seleccionada por ROOT; contrato propuesto pendiente de revisión, QA y adopción canónica.

| Campo | Valor |
|---|---|
| Estado | aprobado: elección validada; adopción documental y release pendientes |
| Opción elegida | O1 |
| Validación | ROOT bajo delegación vigente; choice-root.receipt.json, selección 2026-10-11T19:45:58.478501+00:00; segunda pasada liberada 19:50:49.001178+00:00 |
| TDD | n/a: prosa; no código, ejecución nativa ni tests |
| FIX1 | B01 confirmado por ROOT; workspace SDK131328, arena K1 n131584/B512, requested132095; revisión/QA/adopción pendientes |
| Alcance del actor | Exclusivamente este design.md; sin canon, ledger, ADR, Git, medidor o runtime |

## 1. Contexto y restricciones

K2 adoptado en `755b476` deja pendiente un emisor real para `_issue_acquisition_admission(deployer_authority, *, scope)` y `_pin_current_acquisition_admission(admission, *, owner)`. El snapshot contiene el acta de adopción documental y su contrato íntegro. No contiene implementación K2 ni K4a.

La cadena finita será bootstrap privado confiable → principal efectivo observado → ratificación nominal del deployer → admisión K4a → adquisición candidata K2 → observación K3 → cadena S1 K4b → I/O K5 → store. K4a no necesita RootContext ni una cadena positiva para permitir lectura de candidatos. No acredita ACL, origen propio de archivos, writer, creación, store o ACK.

[S1](../2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md) ya confía en deployer, controller, principal autorizado, SYSTEM y administradores. Excluye la promesa de protegerse de código hostil con el mismo SID. Esta propuesta utiliza esa frontera existente. No introduce autenticación remota, cambio de usuario ni un emisor K6 cuya legitimidad quede indefinida.

La legitimidad del emisor procede del código confiable del bootstrap local, ejecutado como controller por el deployer dentro de esa frontera. La observación del SID identifica su contexto efectivo; no demuestra por sí sola la autorización del despliegue. No se pretende demostrar la integridad del código mediante su propia introspección, un path o su digest.

El runtime `scripts/storage_journal_windows.py:260`, `current_security_principal()`, ya consulta TokenUser y rechaza tokens de thread. Su retorno de bytes no es DeployerAuthority. No consulta primary group ni emite registros K4a. U2 conserva su alcance readonly.

`scripts/storage_operator.py:129`, PublishedDiskBinding, y `scripts/storage_receipt_store.py:108`, ReceiptLease, tampoco son bootstrap de autoridad. No se promocionan sus handles, DTO o snapshots. K1 conserva su custodia y poison; sus contexts no ratifican principal.

El host mantiene el resultado documentado de MODIFY outsider: full-chain S1 continúa rechazando. El principal observado no limpia ancestros. Constitución §2 veta nuevo servicio sin ADR, escrituras SQLite desde controller y almacenamiento fuera del proyecto. No se propone ninguno.

## 2. Opciones (2)

### O1 — Bootstrap privado del controller y principal de su proceso actual

Un único bootstrap privado del controller inicia la sesión K4a en su propio proceso Windows x64. Su entrada cerrada no acepta SID, cuenta, path, flags, backend, DTO ni un authority aportado por el caller. El deployer ejecuta código confiable según la precondición explícita S1; no existe una segunda autoridad que haya que acreditar después.

Ese bootstrap registra primero un `_NativeIssuer` exacto de provenance interna `native_windows_x64`. Su record aporta PID observado, estado inicial y una custodia mínima para consultar sólo los tokens propios. No permite K2 ni abre archivos. Así la consulta inicial no exige una admisión que todavía no puede existir.

Tras observar ausencia de impersonación y el token primario actual, el bootstrap registra `_EffectivePrincipalObservation`. A continuación registra `_DeployerAuthority` nominal vinculada por identidad al issuer, al proceso y a esa observación. Ese acto privado expresa la ratificación del deployer de su propio contexto actual dentro de S1. Los bytes del SID nunca entran como parámetro autoritativo.

La misma sesión registra `_SecurityPolicy` y `_PolicyEpoch` vivos con doctrina S1 fija. `_issue_acquisition_admission` recibe únicamente la DeployerAuthority auténtica y el scope enum exacto. Registra `_AcquisitionAdmission` con todos los campos exigidos por K2 §4.2. Una política/epoch distinta, obsoleta o no registrada rechaza.

Cada frontera K2 solicita un pin nuevo en el thread que ejecutará la llamada. El observador nativo de tokens propios revalida issuer/authority vivos sin llamar recursivamente al pin K2. El pin registra owner, admission, PID, thread, principal/group y policy/epoch por identidad. Retiene el contexto hasta reconocer la frontera y su salida completa.

Cambios de token, principal/group, epoch o revocación bloquean nuevas ENTRY. Un thread nuevo obtiene su propia observación y pin; no reutiliza el pin de otro thread. La observación no concede derechos de impersonación. Todo token de thread, incluso con el mismo SID, rechaza; no se usa RevertToSelf para obtener un positivo.

El bootstrap puede habilitar `CANDIDATE_READ_ONLY` y `PRODUCT_CHAIN_CANDIDATE`, según el enum privado ya adoptado. El segundo describe profiles potenciales; CREATE sigue exigiendo guard `_ParentS1Admission` de K4b. `OWNED_PROBE_CANDIDATE` continúa cerrado hasta el contrato K5.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: registro local, observaciones actuales, epochs, pins y custodia sin transporte |
| Riesgo | Interpretar autoobservación como ratificación; se evita separando observación del acto privado del bootstrap confiable |
| Coste relativo | S frente a O2; no presupone que las queries SDK o los cortes de custodia sean triviales |
| Reversibilidad | Alta antes del wiring: conserva los seams consumidores K2 y ninguna authority cruza procesos |

### O2 — Bootstrap confiable que supervisa un hijo propio y lo ratifica por atestación local

El mismo deployer confiable inicia un supervisor local y un hijo controller propio mediante una ruta cerrada. El supervisor registra el hijo por el handle real que obtiene de su creación, no por un PID aportado, nonce copiado o nombre del ejecutable. No arranca bajo otra cuenta ni activa privilegios.

La legitimidad termina igualmente en el bootstrap local S1. El supervisor no se deriva del journal ni de una authority futura. Retiene la instancia del hijo y compara su token primario observado con el contexto legítimo del lanzamiento. El hijo observa su proceso/thread actuales con las mismas restricciones O1.

El supervisor sólo autoriza esa instancia mediante un canal privado con endpoints propios, procedencia de creación y custodia acreditadas. Un mensaje serializado expresa una solicitud o una atestación; no es `_DeployerAuthority`. El hijo registra una nueva authority local únicamente tras acreditar emisor, instancia, canal vivo y observaciones actuales concordantes.

En el hijo, issuer/authority/policy/epoch/admission/pin siguen usando tipos y registros locales exactos. Ningún objeto Python del padre conserva autoridad al ser copiado o serializado. La muerte, revocación o incertidumbre del supervisor/canal cierra admisión. Reinicio del hijo requiere otra atestación, registros y epoch nuevos.

Cada frontera nativa mantiene consulta propia y pin por thread como O1. El supervisor añade detección de ciclo de vida y una retirada verificable del hijo, útil si esa separación ya fuese necesaria para poison. No evita el requisito de ausencia de impersonación ni el full-chain S1 del host.

Esta opción es implementable dentro de procesos propios y sin servicio persistente. Exige cerrar creación del hijo, custodia del handle de proceso, canal, protocolo de atestación y revocación antes del RED. No se presenta un pipe con nonce como prueba suficiente. Su beneficio es aislar la vida del controller y la ratificación entre instancias; no resistir código hostil del mismo principal.

Scopes y guard CREATE son exactamente los de O1. El supervisor no emite RootContext, parent guard, WriterLease, store o ACK. No sustituye K4b ni ratifica ACL de ancestros.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: lanzamiento, dos registros, canal atestado, handle de hijo, revocación y reap |
| Riesgo | Confundir transporte con capability o aceptar un hijo por PID reutilizado; exige identidad/custodia reales |
| Coste relativo | L frente a O1; amplía el bootstrap y las fronteras nativas que requieren contrato y QA |
| Reversibilidad | Media: mantiene el seam K2, pero cambia el despliegue y la gestión de vida del controller |

## 3. Criterios de decisión

1. Cerrar una cadena de autoridad finita apoyada en la frontera confiable S1 ya aprobada.
2. Mantener exactos los seams K2, scopes y guard CREATE, sin exigir chain trust antes de leer candidatos.
3. Revalidar contexto efectivo, principal/group y policy/epoch actuales en cada frontera y thread.
4. Preservar custodia ante cuts post-TRUE; ninguna consulta o cierre incierto permite retry ni otro owner sano.
5. Separar assemblies CPU de emisor nativo y conservar calls0 antes de cargar bindings K2 sin admission auténtica.
6. Preferir la menor extensión del bootstrap que satisfaga esos contratos. El aislamiento de procesos sólo compensa si su necesidad es legítima y concreta.

## 4. Recomendación · opción elegida y por qué

**Recomiendo O1.** S1 ya presupone controller y deployer confiables. O1 concreta esa raíz en el bootstrap privado y observa su principal efectivo actual. Cumple los criterios 1, 2, 3 y 5 sin construir otro protocolo de autoridad.

**Opción elegida: O1**, por ROOT bajo delegación vigente del propietario. O2 queda descartada para emisión K4a: añade atestación entre procesos sin una necesidad acreditada de transporte de autoridad. Un supervisor propio seguirá siendo necesario para retirada/reap ante poison o agotamiento. No será emisor ni autenticador K4a. La separación de procesos no arregla los ancestros del host.

### 4.1 Raíz finita, bootstrap legítimo y pared de callers

La raíz es el controller local confiable que ejecuta el deployer según S1. No existe un issuer upstream adicional. La precondición de código confiable ya está declarada en S1 y en el store O2. K4a no demuestra por introspección que el despliegue respete esa precondición; tampoco promete proteger Python frente a código hostil interno.

`_bootstrap_current_deployer() -> _DeployerAuthority` es la única entrada de emisión inicial. Es privada, sin argumentos y sin wrapper CLI/HTTP público. Sólo el arranque cerrado del futuro controller invoca esa entrada una vez por proceso. Los callers readonly actuales no la invocan ni reciben su resultado. No hay parámetro `trusted`, SID esperado, epoch, backend, nonce, hash o authority externa.

La entrada primero registra `_IdentitySession` y `_NativeIssuer` en estado building, PID actual y provenance interna. Con esos records, gate Windows AMD64 y poison común limpio, carga bindings propios y crea una arena K1 de longitud131584 y alineación512 para el workspace SDK lógico131328 de §4.5. Valida y carga requested132095 antes de ENTRY; reserva el tail256 sin convertirlo en output SDK. Su permiso mínimo sólo permite consultar tokens propios y custodiar sus recursos. No exige `_AcquisitionAdmission` ni `_AdmissionPin`; no abre archivos.

La observación inicial completa confirma el contexto efectivo actual. Entonces el bootstrap registra policy S1 immutable, epoch única y `_DeployerAuthority`. La referencia `principal_ratification_ref` será esa misma authority auténtica. Registrar la authority es el acto privado del bootstrap que ratifica su propio contexto observado. No es una transformación de un SID aportado por otra API.

Una segunda invocación del bootstrap, import reload o intento de reconstruir records rechaza `OWNER_RETIRE_REQUIRED` antes de bindings. La entrada inicial se marca consumida incluso si su bootstrap falla de forma conocida. La marca vive en el dominio K1 del proceso, no en un módulo identity recargable. Un restart no hereda autoridad; requiere bootstrap y observación nuevos.

### 4.2 Firmas privadas y estado nominal

Estas firmas son contrato propuesto para implementación futura. Ninguna ejecuta ahora. Sus tipos opacos usan slots; no hay constructor público útil, int, buffer protocol, copy/deepcopy o pickle con autoridad. `object.__new__`, subclass y duck typing sin entrada auténtica rechazan. Registry lookup valida `type(x) is T`, `record.capability is x`, session/issuer vivos, PID y provenance.

| Firma cerrada | Entrada y efecto |
|---|---|
| `_bootstrap_current_deployer() -> _DeployerAuthority` | Raíz privada de §4.1; no inputs autoritativos |
| `_issue_acquisition_admission(deployer_authority: _DeployerAuthority, *, scope: _AdmissionScope) -> _AcquisitionAdmission` | Authority auténtica live; observación nueva concordante; scope exacto permitido; registra antes de retornar |
| `_bind_acquisition_owner(admission: _AcquisitionAdmission, *, owner: _AcquisitionOwner) -> None` | Sólo la factory K2: owner building auténtico de su registro nativo, admission_ref exacta, mismo PID/source; vínculo registrado una vez |
| `_validate_current_admission(admission: _AcquisitionAdmission) -> None` | Validación pura nominal/registro/policy/epoch/PID/poison para precheck K2 antes de cargar sus DLL; no query ni grant |
| `_pin_current_acquisition_admission(admission: _AcquisitionAdmission, *, owner: _AcquisitionOwner) -> _AdmissionPin` | Vínculo/frame/leases auténticos K2 con boundary y owner ya bloqueados; toma sesión, observa contexto actual y registra pin/thread |
| `_complete_acquisition_admission_pin(pin: _AdmissionPin, *, owner: _AcquisitionOwner) -> None` | Mismo owner y thread; postobservación completa; consume pin y su lock lease, sin emitir authority de archivo |
| `_abort_acquisition_admission_pin(pin: _AdmissionPin, *, owner: _AcquisitionOwner) -> None` | Error primario retenido por K2; misma custodia del pin. Retorno backend incierto exige poison, no una postobservación que invente éxito |
| `_revoke_deployer_authority(deployer_authority: _DeployerAuthority) -> None` | Revocación pura bajo locks; invalida epoch, admissions y pins dependientes; idempotente |
| `_close_deployer_authority(deployer_authority: _DeployerAuthority) -> IdentityCloseOutcome` | Cierre explícito §4.9; nunca destructor/finalizer con calls nativos |
| `_identity_info(deployer_authority: _DeployerAuthority) -> IdentityInfo` | DTO sin SID, handles, pointers, thread ID, nonce, registry, backend o token LUID |
| `_observe_current_effective_principal(session: _IdentitySession) -> _EffectivePrincipalObservation` | Sólo bootstrap/issue/pin/complete internos; permiso nominal tokens propios, no admisión K2 recursiva |

`_AdmissionScope` es Enum privado propiedad del módulo identity, compartido por imports exactos K2. Sólo `CANDIDATE_READ_ONLY` y `PRODUCT_CHAIN_CANDIDATE` emiten admission. `OWNED_PROBE_CANDIDATE` rechaza `ADMISSION_REQUIRED` antes de native query; se reserva a K5 sin liberarlo.

| Record fuerte | Campos privados exactos |
|---|---|
| `_IdentitySessionRecord` | capability,issuer_ref,pid:int,source literal,state enum,workspace_context,workspace_arena,workspace_sdk_length:int,workspace_k1_length:int,workspace_alignment:int,workspace_requested:int,workspace_tail:int (constantes §4.5),policy_ref,epoch_ref,authority_ref,lock:RLock,threads,admissions,pins,observations,calls,counters,outcome |
| `_NativeIssuerRecord` | capability,session_ref,pid,source,bindings_ref exacto,state; nada del caller determina bindings |
| `_DeployerAuthorityRecord` | capability,session_ref,issuer_ref,pid,principal_sid:bytes,primary_group_sid:bytes,ratification_observation_ref,token_stamp,policy_ref,epoch_ref,state |
| `_EffectiveObservationRecord` | capability,session_ref,issuer_ref,pid,thread_ref,thread_id:int,principal_sid:bytes,primary_group_sid:bytes,token_stamp,policy_ref-or-None,epoch_ref-or-None,state,frame_ref |
| `_SecurityPolicyRecord` | capability,session_ref,issuer_ref,doctrine literal storage-nt-security-s1,state; no mutable masks/allowlist del caller |
| `_PolicyEpochRecord` | capability,session_ref,policy_ref,issuer_ref,pid,state; identidad de objeto, no integer externo |
| `_AdmissionRecord` | capability,issuer_ref,pid,scope,principal_sid,primary_group_sid,principal_ratification_ref,effective_context_ref,source,policy_ref,epoch_ref,state; exactamente K2 §4.2 |
| `_AdmissionPinRecord` | capability,admission_ref,owner_ref,session_ref,pid,thread_ref,thread_id,principal_sid,primary_group_sid,pre_observation_ref,post_observation_ref-or-None,policy_ref,epoch_ref,state,session_lock_lease_ref,target_frame_ref,boundary_lease_ref |
| `_TokenStamp` | TokenId,AuthenticationId,ModifiedId como pares `(LowPart:uint32,HighPart:int32)`; TokenType literal TokenPrimary |
| `_TokenCallRecord` | ordinal,function enum,phase,session_ref,frame_ref,input/output ranges propios,preimage,raw_result-or-None,error:uint32-or-None,recognized_handle-or-None,close_attempted:bool |

References authority/policy/epoch son objetos opacos registrados. Los counters son int exactos no negativos con límites §4.8. `bool` no sustituye int. Los estados capability externos son live/revoked/unknown/closed. Records internos añaden building/reserved/entered/returned/recognized; nunca se publican en esas fases.

La observación inicial admite policy_ref/epoch_ref=None sólo mientras session building. No sale como admission. El bootstrap la vincula a policy/epoch nuevos bajo lock antes de pasar authority y session a live. Las observaciones posteriores exigen referencias registradas live y no cambian de policy/epoch.

### 4.3 Dominio de poison único e interop K1/K2

**BEGIN ROOT CANDIDATE K1/K2 COORDINATION ADDENDUM.** Esta subsección propone la coordinación necesaria para integrar K4a. No modifica bytes canónicos ni afirma que el runtime K1 actual ya la implemente. ROOT deberá ratificarla como concreción antes del RED que dependa de ella.

El poison único es el módulo canónico `scripts.storage_journal_windows_io` ya importado y su `_KERNEL_POISONED`, bajo `_REGISTRY_LOCK`. Identity importa esa instancia por nombre relativo normal; no crea otra copia por spec_from_file_location, import alias o snapshot runtime alternativo. No hay `_IDENTITY_POISONED` sano independiente.

Se proponen en el mismo módulo K1 `_NATIVE_BOUNDARY_LOCK:RLock` y los seams `_kernel_domain()`, `_kernel_domain_poison_identity(session)` y `_kernel_identity_bootstrap_claim()`. El primero toma ese lock de frontera, comprueba poison con una sección breve `_REGISTRY_LOCK` y emite `_KernelBoundaryLease` exacta de ese thread/PID. Mantiene sólo el lock de frontera durante la operación. El segundo valida sesión identity registrada, pone ese mismo `_KERNEL_POISONED=True` y retiene la sesión incierta. El tercero consume la latch de bootstrap antes de DLL. Ninguno recibe un dictionary, flag trusted o backend del caller.

`_LIVE_IDENTITY_SESSIONS`, `_QUARANTINED_IDENTITY_SESSIONS`, `_CLOSED_IDENTITY_SESSIONS` y la latch viven junto a `_QUARANTINED_MEMORY_CONTEXTS`, bajo el registry común. Retienen session/issuer/bindings/workspace/calls/outputs/tokens/pins/admissions/owner_refs fuertes. La validación usa `_registered_native_session(session)` exacto, sin callback del caller. El registro no es una factory. Recargar identity no elimina esa custodia ni permite otro bootstrap; capabilities de clases recargadas no coincidentes rechazan y exigen retirada.

El orden propuesto será `_NATIVE_BOUNDARY_LOCK` → owner K2.RLock, si existe → session K4a.RLock → context K1.RLock. El registry sólo sirve para lookup/estado/pins breves y siempre se suelta antes de esperar un RLock. Se retiene el lock de frontera durante query o pin/backend/postcheck. Reentradas internas usan RLock en el mismo thread; no invocan callbacks públicos.

K2 §4.11 ya exige owner.RLock alrededor de cada backend/reconocimiento y suelta el registry antes de esperarlo. El nuevo preludio del guard K2 toma boundary antes de su lookup/owner lock; no cambia esa regla. `_pin_current_acquisition_admission` recibe el owner ya bloqueado y exige una lease boundary auténtica en el call frame preregistrado. No toma boundary ni owner después. Sólo toma session lock. Frame/lease faltante devuelve CAPABILITY_INVALID/calls0; no intenta arreglar el orden tomando locks inversos.

Bootstrap/issue/revoke/close toman boundary y session, sin esperar un owner lock desde session. Revocar cambia records identity/epoch/admission; no escribe records K2 sin su owner lock. K2 descubre la revocación bajo su propio guard. Cerrar authority consulta únicamente resúmenes terminales de owners vinculados, sin tomar sus locks; si no constan cerrados, retira/rechaza. Así no hay ciclo session→owner frente a owner→session.

La integración K1 debe anteponer boundary a sus factories y a `_pinned` cuando una operación pueda invocar backend nativo. Conserva lookup registry breve, después context lock, y mismo poison. K1 de memoria no pide principal/admission K4a ni privilegios adicionales. Sus info puros pueden seguir sin boundary. Esta coordinación no existe hoy; exige TDD causal y regresión whole de K1 al implementarla.

El workspace usa sin relajar C2 `_allocate_aligned(context, length=131584, alignment=512)`: carga K1 `(count=1,logical_bytes=131584,requested_bytes=132095)` y conserva un único backing compartido con la sesión K4a. Aquí logical_bytes de K1 significa longitud de arena, distinta de los131328 bytes SDK lógicos. El pin identity limita sus rangos al layout SDK de §4.5; ni el tail256 ni el margen de alineación511 son outputs, ReturnLength o destinos SID. Los resúmenes K4a referencian esa misma carga; sumarla otra vez por ser compartida inventaría un segundo backing. Unknown conserva toda la carga y custodia; sólo rollback/free conocido puede retirarla. El apéndice añade coordinación futura, sin cambiar la policy de alineación, cuotas, overflow o custodia K1 ya aceptada.

Con el apéndice implementado, las ENTRY nativas K1/K2/K4a usan boundary y el mismo poison. Poison K1 impide bootstrap/query/pin K4a y factories/backend K2. Poison K4a impide alloc/copy/free K1, opens/closes K2 y refresh. Tras poison sólo info, revocación y outcomes puros; ningún nuevo close/free/query ni reset del latch. El runtime K1 actual comparte flag, pero no se atribuye este lock nuevo a sus caminos existentes.

K2 valida admission antes de cargar sus bindings. Sin issuer/admission auténticos: `ADMISSION_REQUIRED`, DLL K2 calls0 y backend calls0. Una vez registrado owner building, K2 registra el vínculo exacto antes del primer pin. Cada frame backend K2 retiene su `_AdmissionPin`; scope/profile y guard parent CREATE se comprueban bajo ese mismo dominio y owner lock.

Los pins no son capabilities K1 de memoria ni grants de archivo. K4a no emite `_ParentS1Admission`, RootContext, ChainLease, OwnedFile, WriterLease o ACK. Guard K4b live actual sigue obligatorio para CREATE_FILE/CREATE_DIRECTORY. El scope read sólo permite ANCHOR_CANDIDATE/PARENT_EXISTING/READ_EXISTING, conforme K2 §4.2.

**END ROOT CANDIDATE K1/K2 COORDINATION ADDENDUM.** Si ROOT considera que este preludio cambia C2/O2 en vez de concretarlo, exige propuesta ADR explícita. No se adopta de forma tácita. El contrato no puede liberar pins nativos sin un protocolo de locks ratificado.

### 4.4 Bindings SDK cerrados y layouts AMD64

Import identity/ABI en Linux permanece puro: no ctypes, DLL, kernel queries o bindings hasta factory nativa tras gate. Gate exige os.name nt, sys.platform win32, Python64, punteros8 y machine amd64/x86_64. ARM64/32bits/ambigüedad rechazan `PLATFORM_UNSUPPORTED`.

`_new_native_identity_backend() -> _IdentityOps` vive en el módulo ABI C2. No acepta inyección ops ni handles. Su `_IdentityOps` native queda asociado al issuer registrado; el assembly CPU tiene factory/tipo distintos. Antes de recursos, valida todos símbolos, firmas, sizes, offsets y alignments. Fallo de binding deja queries/alloc/opens0.

| DLL / función | argtypes → restype | Inputs fijos |
|---|---|---|
| kernel32 / GetCurrentProcess | `() -> HANDLE` | Contexto propio, pseudo-handle; no se cierra |
| kernel32 / GetCurrentThread | `() -> HANDLE` | Thread propio, pseudo-handle; no se cierra |
| advapi32 / OpenThreadToken | `(HANDLE,DWORD,BOOL,PHANDLE) -> BOOL` | Thread actual, TOKEN_QUERY=8, OpenAsSelf=1, output NULL |
| advapi32 / OpenProcessToken | `(HANDLE,DWORD,PHANDLE) -> BOOL` | Proceso actual, TOKEN_QUERY=8, output NULL |
| advapi32 / GetTokenInformation | `(HANDLE,int32,PVOID,DWORD,PDWORD) -> BOOL` | Clases1/5/8/10 únicamente; sizing NULL/0; fetch fija4/56 o variable<=65536 dentro de su subbuffer SDK, nunca tail K1; ningún TokenSource |
| kernel32 / CloseHandle | `(HANDLE) -> BOOL` | Sólo token propio reconocido del call record |

HANDLE/PVOID tienen width8; BOOL/int32 y DWORD/uint32 width4; PHANDLE/PDWORD son pointers typed. No restype por defecto, c_ulong dependiente de host, `_pack_` artificial o structs importados de U2.

| Estructura | Size/alignment | Offsets |
|---|---|---|
| LUID | 8/4 | LowPart0:uint32, HighPart4:int32 |
| SID_AND_ATTRIBUTES / TOKEN_USER | 16/8 | Sid0:PVOID, Attributes8:uint32; padding12..15 sin semántica |
| TOKEN_PRIMARY_GROUP | 8/8 | PrimaryGroup0:PVOID |
| TOKEN_TYPE | 4/4 | TokenPrimary=1; TokenImpersonation=2 rechaza |
| TOKEN_STATISTICS | 56/8 | TokenId0,AuthenticationId8,ExpirationTime16:int64,TokenType24:int32,ImpersonationLevel28:int32,DynamicCharged32:uint32,DynamicAvailable36:uint32,GroupCount40:uint32,PrivilegeCount44:uint32,ModifiedId48 |

TokenInformationClass fija TokenUser=1, TokenPrimaryGroup=5, TokenType=8 y TokenStatistics=10. No consulta TokenImpersonationLevel para un token primario: ese campo sólo tiene semántica para impersonation tokens. ExpirationTime y counts no se convierten en permisos.

Los tamaños son contrato deducido de definiciones SDK documentadas. La alineación8 de structs/slots SDK es independiente de B512 exigido por el allocator K1. Una base alineada512 cumple también align8; los offsets de §4.5 conservan sus alignments originales. No se reinterpretan ni amplían las estructuras para satisfacer K1. El release futuro debe acreditarlos con ctypes real Windows y queries propias. No se afirma un ABI probado hoy ni una versión de SDK instalada.

### 4.5 Workspace propio, límites y salida sin pointers

La sesión adquiere un context K1 nominal y una arena propia sólo después de bindings completos. El workspace SDK lógico sigue siendo L=131328 bytes:256 de control y dos query buffers de65536. La llamada compatible con C2 es `_allocate_aligned(context, length=131584, alignment=512)`. Su longitud de arena es `n=ceil(L/512)*512=131584`, con `n%512=0`; solicita exactamente `r=n+B-1=132095` bytes al backend K1. El tail lógico de arena es `n-L=256`, y el margen de ajuste de dirección es `B-1=511`. Es memoria volátil propia, no archivo. Las operaciones K1 entran por sus factories/calls exactos; no se usa VirtualAlloc/VirtualFree paralelo ni arrays SDK fuera del ledger.

Antes de ENTRY se validan int exactos, constantes/layout, B512 permitido, n positivo/múltiplo, límites C2 y overflow. Para calcular el redondeo se comprueba `L<=SIZE_T_MAX-(B-1)` antes de sumar; para r se conserva `_checked_reservation_size(n,B,SIZE_T_MAX)`. Tras retorno se mantienen los guards K1 de base original `b>0`, `b+r<=SIZE_T_MAX`, dirección `a=(b+B-1)&~(B-1)`, `a%B=0`, `a>=b` y `a+n<=b+r`. Ningún scalar inválido se utiliza para construir un pointer, copiar o liberar.

| Nivel / intervalo semiabierto | Longitud y uso |
|---|---|
| SDK lógico `[a,a+131328)` | L131328; sólo los segmentos SDK de la tabla siguiente |
| Arena K1 `[a,a+131584)` | n131584; contiene el SDK más tail256 |
| Tail `[a+131328,a+131584)` |256; padding final sin output SDK, ReturnLength, SID ni copia de payload |
| Solicitud backing `[b,b+132095)` | r132095; un único backing; carga requested K1, sin afirmar reserva/commit físico OS |
| Margen fuera de arena | Prefijo `d=a-b` entre0 y511, sufijo `511-d`; total511; ninguno es rango SDK |

Ejemplo aritmético, no ejecución: con `b=4097`, `a=4608`, `d=511`, `a+n=b+r=136192`; el SDK termina en135936 y el tail256 termina en136192. Con b alineada512, d0 y el margen511 queda al final del backing. En ambos casos r-L=767 son256 tail más511 de margen, no una tercera query buffer. No se supone que VirtualAlloc devuelva esa base ni se exige allocator reuse.

Las copias usan `_arena_copy_in(context,arena,offset=...,data=bytes)` y `_arena_copy_out(context,arena,offset=...,length=...)`, existentes. El seam nuevo `_pin_identity_workspace(session: _IdentitySession, arena: AlignedArena) -> _IdentityWorkspacePin` vive en IO. Comprueba session nativa registrada, context/arena auténticos asociados por identidad, PID/source/state y metadata exacta L131328/n131584/B512/r132095/tail256. Emite un pin privado para el frame actual; sus ranges sólo admiten segmentos de la tabla SDK y `offset+length<=L`, aunque la arena K1 permita n. Comprueba con resta acotada, no suma susceptible de overflow. El binding no recibe un address del caller ni admite workspace CPU en native.

`_IdentityOps.execute(call: _TokenCallRecord) -> _TokenBoolResult-or-_ContextPseudoResult` valida el call exacto preregistrado, permit/frame/workspace pin, ordinal entered y función enum cerrada. El dispatcher toma argumentos y outputs del record propio. No recibe HANDLE/pointer/access mask/function name externo. `_ContextPseudoResult` es privado y nunca sirve como handle owned. CPU tiene `_CpuIdentityOps.execute(_CpuTokenCallRecord)` de tipo distinto y storage propio, sin dereferencias a addresses ficticios.

| Rango SDK lógico relativo a a, extremos inclusivos | Uso exclusivo y alineación |
|---|---|
| 0..31 | Cuatro HANDLE output slots de8: thread_pre,process_first,process_current,thread_post; align8 |
| 32..55 | Seis ReturnLength DWORD slots: stats_before,type,user,group,stats_after,stats_current; align4 |
| 56..59 | TOKEN_TYPE output de4, align4 |
| 60..63 | Padding propio |
| 64..119 | TOKEN_STATISTICS before de56, align8 |
| 120..175 | TOKEN_STATISTICS after de56, align8 |
| 176..231 | TOKEN_STATISTICS current de56, align8 |
| 232..255 | Reserva fija sin llamadas |
| 256..65791 | TokenUser output máximo65536, align8 |
| 65792..131327 | TokenPrimaryGroup output máximo65536, align8 |

K1 copia las preimágenes sólo a los segmentos SDK del workspace antes de ENTRY. HANDLE output inicia NULL; ReturnLength0; type0x7fffffff; buffers variables/fijos con sentinel0xA5. Los pointees son ventanas del backing propio y permanecen retenidos. Las views ctypes sólo apuntan a esos segmentos; no crean otros arrays de output. El tail256 no se inicializa, captura o interpreta como dato SDK. Padding de control60..63/232..255, padding interno de structs y tail K1 tienen papeles separados; ninguno amplía una fetch.

Cada sizing usa output pointer NULL y length0. Exige FALSE con ERROR_INSUFFICIENT_BUFFER=122 y ReturnLength válida. Los máximos variables siguen siendo65536; mínimos user28 y group20. Para TokenType/Statistics, sizing debe indicar exactamente4/56. Una fetch usa sólo la capacity pedida y validada del subbuffer actual, nunca n, r, L ni el tail para ampliar el output. Exige TRUE y ReturnLength exacta4/56 para outputs fijos, o entre mínimo y esa capacity<=65536 para variables. User y group no pueden cruzar su límite, entrar en el otro subbuffer o alcanzar padding. No resize/retry si el tamaño cambia; rechaza y revoca.

El parser lee primero bytes del header validado mediante copia K1. Sólo después interpreta Sid/PrimaryGroup como uint64 privado. Aquí base es la dirección inicial del subbuffer SDK consultado, no b ni a global. Exige pointer>=base+header_size, pointer%4=0 y al menos8 bytes SID dentro de `[base,base+ReturnLength)` de esa fetch reconocida. Calcula longitud SID `8+4*subauthority_count` con count1..15, revision1; exige intervalo íntegro y copia exactamente esa longitud. La arena mayor no legitima pointers al otro query buffer, al tail o al margen de alineación. Ningún memmove/string_at/getter recibe pointer que aún no pasó bounds.

TokenUser.Attributes debe ser0: no existen atributos user SID definidos en la fuente fijada. La reserva/padding SDK no se interpreta ni se exige que quede escrito. IdentifierAuthority son sus6 bytes exactos, sin traducción de cuenta, comparación textual o prefijo. Primary group sólo proporciona GROUP, sin extender trustees S1.

No se publica arena address, pointer, HANDLE, SID, token IDs o datos personales. `_EffectivePrincipalObservation` es opaco. `IdentityInfo` sólo copia state/source, counts acotados y scope names; no se puede promover ese DTO a authority/admission.

### 4.6 Observación efectiva actual sin dependencia circular

Un `_TokenObservationPermit` exacto interno retiene issuer/session/workspace, PID, thread_ref/thread_id, policy/epoch y ordinal del plan. No acepta callables, funciones SDK o parámetros del caller. Se preregistra bajo dominio antes de las llamadas. Building permite sólo observación inicial; live permite issue/pin/postcheck. Cleanup conocido permite sólo cerrar tokens ya reconocidos del propio frame.

| Paso fijo | Comprobación y resultado |
|---|---|
| Q0 | Gate/session/issuer/poison/quota y workspace exacto L131328/n131584/B512/r132095/tail256; leer os.getpid(), threading.get_native_id() y current_thread() propios; preregistrar frame/rangos SDK/plan |
| Q1 | GetCurrentThread y OpenThreadToken pre; sólo FALSE/error1008/outputNULL demuestra ausencia. TRUE con handle válido reconoce recurso y rechaza impersonación |
| Q2 | GetCurrentProcess y OpenProcessToken first; TRUE/handle real reconocido |
| Q3 | TokenStatistics before: sizing+fetch; TokenType interno1 y stamp actual |
| Q4 | TokenType: sizing+fetch; valor1 y concordancia con stats |
| Q5 | TokenUser: sizing+fetch, parser SID cerrado |
| Q6 | TokenPrimaryGroup: sizing+fetch, parser SID cerrado |
| Q7 | TokenStatistics after: sizing+fetch; mismo TokenId/AuthenticationId/ModifiedId y type1 que before |
| Q8 | GetCurrentProcess nuevamente y OpenProcessToken current sobre proceso propio; otro handle real, mismo token esperado; TokenStatistics current sizing+fetch; mismo stamp |
| Q9 | GetCurrentThread y OpenThreadToken post; misma ausencia inequívoca. Si aparece token, reconocerlo y rechazar, sin cambiarlo |
| Q10 | Cerrar tokens propios conocidos en orden inverso de adquisición, cada uno una vez; verificar outputs/return/terminal outcome completo |
| Q11 | PID/thread_ref/thread_id/issuer/policy/epoch iguales; registrar observación opaca con SID/group/stamp y frame conocido; publicar sólo tras Q10 |

No se consulta otro PID ni handle externo. Los pseudo-handles de proceso/thread no ocupan slots de tokens propios ni se cierran. Los outputs token rechazan NULL, INVALID_HANDLE_VALUE y la banda de pseudo-handles uint64>=2^64-6. Dos outputs vivos con el mismo valor numérico producen RESOURCE_UNKNOWN: no se supone que representan dos recursos cerrables.

Antes de cada SDK ENTRY del plan, el permit contrasta PID/thread_ref/native_id propios, state, policy/epoch si existen, poison, ordinal y rangos SDK dentro de L y del subbuffer actual; n/r no amplían esos rangos. Estos checks locales no son un pin K2 recursivo ni una observación OS nueva completa por cada subquery. La ausencia de impersonación se acredita al principio y al final de la secuencia; cada frontera K2 recibe además una secuencia completa pre y post.

El API BOOL nativo acepta cualquier int32 no cero como TRUE, no sólo1. Su wrapper produce `_TokenBoolResult(success:bool,error:uint32-or-None)` exacto. Captura el LastError thread-local inmediatamente sólo en FALSE mediante WinDLL(use_last_error=True); en TRUE error=None. No realiza otra API ni cleanup antes de capturarlo. Un double de tipo incorrecto tras ENTRY es outcome unknown; no un FALSE inventado.

FALSE/error1008 con token outputNULL sólo es esperado en OpenThreadToken. FALSE/error122 con ReturnLength válida sólo es esperado en sizing. AccessDenied/anonymous token/otro error no prueban ausencia de impersonación. FALSE con token output no NULL o sizing TRUE incoherente rechazan; output adquirido/incierto conserva custodia, sin cerrarlo por deducción.

Un fallo conocido de fetch o rechazo SID después de abrir tokens conserva esa causa primaria y cierra sólo handles propios ya reconocidos. Si esos cierres son completamente conocidos, devuelve PRINCIPAL_UNACCREDITED y revoca sesión. Una query que retorna TRUE con bytes malformed puede rechazarse de forma conocida si la llamada y todos sus outputs fueron reconocidos; no permite emitir observación. Un cut antes de completar ese reconocimiento es unknown aunque el SDK sólo haya leído.

### 4.7 Pins actuales, epoch immutable y revocación

Bootstrap conserva como baseline los SIDs y stamp iniciales. Issue hace observación completa nueva y exige baseline vigente. Los pins exigen SID/group/TokenId/AuthenticationId/ModifiedId exactos contra authority/admission y policy/epoch por identidad. Un cambio íntegramente observado devuelve PRINCIPAL_UNACCREDITED, revoca authority/epoch/admissions y no continúa la sesión con un nuevo SID.

`threading.current_thread()` se observa internamente y se retiene por referencia; native_id debe coincidir hasta completar el pin. Eso evita aceptar un thread distinto cuyo identificador fue reutilizado. El pin sólo puede completarse/abortarse en ese thread. Transferencia a otro thread rechaza antes del backend y conserva el pin; nunca libera un RLock desde un thread ajeno.

`_pin_current_acquisition_admission` recibe boundary y owner lock ya mantenidos por el guard K2 registrado. Toma session lock, hace Q0..Q11 pre y registra pin/cuotas antes del SDK K2. Retiene sólo su lease adicional session hasta complete/abort. K2 guarda el pin en su frame preregistrado y ejecuta una sola frontera backend. Complete hace Q0..Q11 post y revalida scope/references; K2 revalida su guard CREATE actual bajo owner lock antes de publicar. Ningún resultado sobrevive a un postcheck rechazado como trusted.

El pin identifica exactamente el target frame propio `owner.inflight`. Para owner live se permiten las operaciones K2 de su scope. Para owner closing sólo frames de cierre explícito de recursos conocidos; admission/epoch deben seguir live. Owner revoked/unknown, frame sin lease, frame ajeno o operación creadora durante closing rechazan antes de ENTRY. Ese permiso de close procede del admission vivo y ownership K2, no de un nuevo grant K4a.

Los locks son leases internas registradas, con máximo1 pin activo. Cut mientras se registra/transfiere una lease produce unknown y poison; el record fuerte conserva thread y refs. No se fuerza unlock de otro thread. El supervisor debe retirar el proceso si queda bloqueado. Error pre-ENTRY completamente reconocido libera sólo la lease session del pin; el guard K2 cierra su owner/boundary en orden inverso, sin backend destino.

Complete consume un pin una vez; repetirlo devuelve resultado terminal puro sin nuevas queries. Después del retorno no se reutiliza el pin en otra frontera. Postcheck con cambio conocido revoca admission y devuelve rechazo; K2 revoca su owner bajo el lock que ya mantiene y conserva el output reconocido. No afirma que la llamada anterior no ocurrió, promueve trust o reintenta.

Policy representa exactamente S1 y es immutable durante la sesión. Epoch es un objeto único por proceso/sesión, sin increment/getter autoritativo o setter. Revocación queda permanente. Cambiar policy, baseline o reinstaurar principal exige otro proceso y bootstrap; no se borra registry ni se emite un epoch sano junto al poisoned.

Pre/post no demuestran ausencia de ABA entre ellos. Se conserva el supuesto S1 de controller y threads propios confiables: ningún thread propio cambia token/impersonación durante un pin. El lock no congela el token Windows ni detiene administradores. Exigir resistencia a esos actores reabriría S1 explícitamente mediante ADR; no forma parte de O1.

### 4.8 Cuotas finitas, tombstones y retirada

| Límite por proceso K4a | Valor y accounting |
|---|---|
| Bootstrap/session/issuer/authority/policy/epoch | Exactamente1 de cada uno; latch lifetime1, nunca reset |
| K1 workspace | Context1, arena1; SDK logical L131328, arena K1 n131584/B512, requested r132095; tail256 y margen511 incluidos. K1 charge(1,131584,132095); K4a referencia el mismo backing, sin sumarlo dos veces |
| Admissions lifetime | 4; máximo2 por cada scope liberado; counts nunca disminuyen por close |
| Owners K2 vinculados lifetime | 4; límite K2 de tombstones sigue independiente; menor cuota aplicable prevalece |
| Threads observados lifetime | 8; references fuertes; ninth rechaza antes de query |
| Pins lifetime / active | 2048 / 1; pin slots reservados antes de su preobservación |
| Observaciones lifetime | 8192; incluye bootstrap/issue/pre/post; reservar2 para cada pin antes de pre; no evicción |
| Subcalls token lifetime | 229376=8192*28; reserva28 por observación; máximo28 slots por frame, incluye pseudo-handle queries y cleanup |
| Handles token simultáneos | 3 reconocidos máximos; cuatro output slots reservados; resultado inesperado conserva slot e incertidumbre |
| Raw frame activo | 1; workspace compartido sólo tras cierre reconocido de todos los tokens y reconocimiento terminal |
| Tombstones | 8192 observaciones,2048 pins,4 admissions,8 threads y1 session/authority/issuer/policy/epoch; mantienen identidad/terminal summary sin handles operativos |

Una observación normal consume22 subcalls:4 consultas pseudo-handle,4 open token,12 GetTokenInformation y2 CloseHandle. Con token de thread post reconocido, un cierre adicional suma23. El máximo28 permite cleanup temprano sin retry; exceder plan reservado antes de ENTRY rechaza. Las queries pseudo-handle no crean recursos cerrables.

Los tombstones retienen cada capability y resultado terminal. Tras éxito conocido se descartan preimages/return buffers transitorios del frame, conservando ordinal/phase/code y referencias de observación/pin. Las summaries tienen esquema fijo, sin tracebacks o inputs arbitrarios. Frames unknown nunca se compactan ni evictan; toda la sesión queda retenida y ya no crece.

El máximo simultáneo de bytes raw copiados por frame sigue siendo262656, dos imágenes del workspace SDK L131328; más SID/group copiados de68 cada uno (136 adicionales). Esas imágenes no capturan el tail256 ni el margen511, y son copias Python separadas del único backing K1 r132095. No se acumulan raw images entre observaciones conocidas. Si se presenta un subtotal de payload/backing solicitado, es `132095+262656+136=394887`, contando el backing una vez; no es cuota nueva ni cota de memoria física, reserva/commit OS, RSS o memoria total Python.

Los counters K1 mantienen sus límites adoptados: n<=1114112, count<=8, sum(n)<=8912896 y sum(r)<=9437176. La sesión workspace carga `(1,131584,132095)` antes de allocate ENTRY; los campos K4a de n/r son referencias de accounting a esa misma carga. El padding entero está incluido en r; no se sustituye r por L, por n ni por un tamaño redondeado por el OS. Durante reserva, adquisición o unknown permanece la carga completa. Un rollback reconocido la retira exactamente; poison/unknown nunca recupera cuota ni permite otro workspace. Tras free completamente conocido, K1 retira la carga operativa una vez. El tombstone conserva n/B/r/tail y outcome para impedir replay, con carga activa0 sólo si el backing ya se liberó de forma conocida. Los counters lifetime de session/observations/pins/admissions/threads nunca disminuyen por ese free.

Agotamiento devuelve OWNER_RETIRE_REQUIRED antes de backend, revoca sesión y exige rotación supervisada. Ningún contador monotónico se reinicia ni se recicla un slot capability. El supervisor conserva la instancia de proceso propio mediante su handle de creación, retira el controller y espera terminate/reap real antes de arrancar otro. PID0/flag `reaped` del caller no bastan.

K4a no implementa autenticación de supervisor ni su lanzamiento. O1 no le pide un authority emisor. El release runtime debe aportar la supervisión propia ya necesaria para retirada K1/K2; si falta, puede rechazar/retener honestamente, nunca continuar con otro owner en el mismo proceso. El contrato interno de K4a queda cerrado sin depender de un issuer posterior.

### 4.9 Custodia, cuts, cierre una vez y memoria

| Cut | Estado y efecto permitido |
|---|---|
| A0, antes de reservar/ENTRY | Error conocido; destino calls0; release sólo de reservas Python conocidas |
| A1, frame/workspace/preimage reservado | Records fuertes completos; n131584/r132095 cargados una vez en K1. Reservas Python del frame pueden retirarse si no ocurrió SDK ENTRY; el backing ya adquirido conserva su carga hasta free conocido K1 |
| A2, entered antes de call | Cualquier excepción desde ese latch hasta reconocimiento completo produce unknown; no deducir que no ocurrió |
| A3, TRUE/handle escrito antes de raw_result/record | Output/frame retenidos incluso sin scalar conocido; process poison; no copiar retrospectivamente un handle para intentar close |
| A4, return reconocido antes de output/rangos/ownership completo | Unknown/poison; conserva workspace y call; sin close/free |
| A5, output y handle record reconocidos | Outcome conocido; sólo siguientes pasos del plan o cleanup conocido propio |
| A6, copy/parse/registro observación interrumpido | Unknown si la frontera/copia entró; no emitir bytes como capability ni recrear record desde buffers |
| A7, registro terminal completo antes del retorno Python | Resultado sólo válido si publication completa; cut en reconocimiento/publicación conserva unknown y no grant |

Los frames/outputs se preregistran y se retienen antes de cada SDK call. Cada handle tiene `close_attempted=False` hasta su ENTRY CloseHandle. Antes de llamar se fija True de forma irreversible. TRUE no produce closed hasta reconocer wrapper, frame y transición terminal. FALSE o cut antes/post-TRUE reconocido completo produce unknown. Repetir close en ese record sólo devuelve su outcome puro; close native attempts<=1.

No se cierran pseudo-handles ni valores inferidos desde outputs de FALSE. El primer close unknown detiene cleanup restante; ningún sibling close ni arena free posterior. La causa primaria de query/validación permanece primera; cleanup unknown se añade como tal y no la reemplaza.

En `_close_deployer_authority`, primero se revocan authority/epoch/admissions/pins. Si hay pin activo, K2 owner no cerrado o cualquier incertidumbre, retorna OWNER_RETIRE_REQUIRED/unknown sin llamadas adicionales. Owner K2 debe cerrar bajo su admission live antes de pedir cierre definitivo de authority; tras revoke, no se inventa un permiso cleanup de archivos.

Si todos los owners K2/pins están terminales conocidos y no hay token abierto, se cierra la única arena n131584/B512/r132095 y su context mediante K1. VirtualFree sigue exactamente su contrato: base original b del backing solicitado, una ENTRY máxima y TRUE reconocido completo; no address alineado a, subbuffer o tail, free repetido o evicción. No se liberan SDK y padding por separado. Un free unknown usa poison K1 y retiene también session identity con carga íntegra132095 y arena131584, incluso si el scalar TRUE llegó antes del reconocimiento terminal. Sólo un cierre conocido permite retirar una vez la carga `(1,131584,132095)`, quitar backing/ops operativos y conservar tombstone puro con sus cifras/outcome; repetir close es outcome puro, sin free ni decremento adicional.

Cleanup de tokens conocidos durante una observación fallida utiliza su permit de ownership, no admission de archivos. Puede completar sus CloseHandle ya planificados tras un rechazo de principal conocido si el dominio sigue limpio. No puede abrir/query nuevos tokens ni hacer llamadas de archivos. Tras poison, incluso ese cleanup queda cerrado.

### 4.10 CPU separado, errores y sanitización

`_assemble_cpu_identity_session(ops: _CpuIdentityOps, *, principal_sid: bytes, primary_group_sid: bytes) -> _CpuDeployerAuthority` es assembly privada de tests. Valida SIDs con el parser puro, source `cpu_double` fija y registros exclusivamente CPU. `_issue_cpu_acquisition_admission(authority: _CpuDeployerAuthority, *, scope) -> _CpuAdmission` y `_pin_cpu_acquisition_admission(admission: _CpuAdmission, *, owner) -> _CpuAdmissionPin` sólo aceptan CPU owner/ops.

K2 conserva `_CpuAdmissionPin` adoptado; identity lo importa como tipo CPU exacto, sin crear un segundo equivalente. `_CpuIssuer`, `_CpuDeployerAuthority` y `_CpuAdmission` nunca son sus tipos nativos. Un dict, flag provenance, nonce, copy, bytes, `_MemoryContext`, `_ObservedHandle`, ReceiptLease, binding o RootContext no los sustituye. Ningún factory CPU admite source native_windows_x64.

Los doubles guardan storage propio bytearrays/offsets, no dereferencian addresses ficticios ni importan ctypes. Campos equivalentes del double prueban parsing y mecánica; no conceden admission nativa. Cap falsa/CPU → native factory K2 devuelve ADMISSION_REQUIRED, DLL0/backend0.

| Código público acotado | Situación |
|---|---|
| PLATFORM_UNSUPPORTED | Gate anterior a ctypes/DLL |
| ABI_UNACCREDITED | Símbolo/firma/layout cerrado falla antes de recursos |
| ADMISSION_REQUIRED | Falta issuer/admission nativa; scope K5 reservado |
| CAPABILITY_INVALID / OWNER_MISMATCH | Tipo/registro/reference/PID/thread inválidos |
| CAPABILITY_REVOKED | Authority/admission/epoch/pin terminal incompatible |
| PRINCIPAL_UNACCREDITED | Impersonación, token cambiado, query incompleta o SID/group malformado reconocido |
| OWNER_RETIRE_REQUIRED | Cuota/latch agotada, recursos no terminales o dominio poisoned |
| RESOURCE_UNKNOWN | Call/close/free/publication/copy que no llegó a reconocimiento terminal |

`IdentityDiagnostic` es frozen: code de tabla, operation enum bootstrap/issue/pin/complete/revoke/close/query, win32_error uint32-or-None, ntstatus=None. `IdentityCloseOutcome` es frozen: state closed/unknown y tuple de diagnostics. No contiene excepción original, buffer, SID, path, handle, backend o tokens; chaining público suprimido. Excepciones originales quedan sólo en custodia unknown fuerte. No se transforma Win32 BOOL en NTSTATUS.

### 4.11 Wiring futuro y frontera readonly

El nuevo `scripts/storage_journal_windows_identity.py` contiene la entrada bootstrap y las factories/records de esta sección. La futura entrada privada del controller será `_bootstrap_journal_principal() -> _DeployerAuthority`, en `scripts/storage_journal.py`; únicamente llama `_bootstrap_current_deployer()` y mantiene su referencia dentro del controller. Se incorporará cuando ROOT libere bootstrap/controller real. No modifica hoy el codec U1 ni convierte sus snapshots en autoridad.

Las APIs existentes `current_security_principal()`, `PublishedDiskBinding.open()`, `ReceiptLease.open_existing()`, `storage_attach.execute()`, `storage_publish.publish_verified_vhdx()` y `storage.main()` no llaman ese seam y no pueden emitir admission. Sus validaciones readonly y CLI administrativas conservan contratos. El futuro caller controller pide admission usando la authority que mantiene; no recibe authority en JSON, argv, env o un argument dict.

La factory K2 `_new_native_acquisition_owner(admission)` mantiene su firma adoptada. Pure precheck identity antes de bindings, vínculo de owner real y pins pre/post son la única integración. No acepta un backend autorizado por un caller, una función `is_trusted()` o hooks públicos. Los fault hooks futuros son privados de tests sobre seams internos sin grants.

No se añaden S1 file trust ni K4b CREATE guard al bootstrap. La consulta del principal puede pasar en el host actual mientras full-chain rechaza SECURITY_UNACCREDITED por MODIFY outsider. Eso es un resultado previsto, no excepción de S1.

### 4.12 Matriz pre-RED y probes futuros propios

Cada criterio funcional exige RED causal antes del código que lo satisface. ROOT debe liberar separadamente implementación y pruebas nativas propias. La matriz no es evidencia ejecutada.

| ID | Criterio/negativo y control positivo | Evidencia futura |
|---|---|---|
| K4a-01 | Import Linux/ARM64/32bit sin ctypes/DLL; Windows AMD64 cerrado | CPU/import real; gate calls0 |
| K4a-02 | Bootstrap una vez, sin SID/flag/backend; latch compartida resiste reload y second call | CPU exact registry; native sólo raíz privada liberada |
| K4a-03 | Dict/subclass/object.__new__/copy/CPU/owner ajeno/PID/thread falsos rechazan | Positivo nominal paralelo, calls0; no grant doble |
| K4a-04 | Todas signatures/sizes/offsets y ReturnLength clases1/5/8/10; structs SDK align8 sobre base K1 align512; tamaños4/56 y variables<=65536 originales | CPU fake DLLs; desalineación/metadata inválida rechaza antes de SDK; ctypes Windows real sin archivo sólo tras ROOT release |
| K4a-05 | ERROR_NO_TOKEN único negativo admitido; access denied/anonymous/outputFALSEnoNULL/TRUEinvalid rechazan | Double causal, no SetThreadToken nativo ni cambio de usuario |
| K4a-06 | TokenUser/group SID pointers dentro/fuera del ReturnLength del subbuffer actual, alignment, length/revision/count y Attributes; pointers a otro subbuffer/tail/margen rechazan aunque estén dentro de backing | CPU bounds pares en último byte permitido y primer byte fuera; fetch65536 positivo/65537 negativo, sin retry; own process native copies sólo tras ROOT release, sin SID publicado |
| K4a-07 | Stats before/after/current ID/Auth/Modified/type cambian; baseline y admission discordantes | CPU secuencias frescas; sin alterar token real |
| K4a-08 | Pin nuevo cada ENTRY K2; impersonación pre/post; thread nuevo válido/transfer/reused ID inválido | CPU barreras deterministas, máximo8 threads; own native threads sólo queries propias |
| K4a-09 | Revocación/epoch/policy cambiada rechazan; readonly candidata sin RootContext | CPU nominal; K2 backend0 al rechazar; sin S1 positiva fabricada |
| K4a-10 | CREATE exige K4b parent guard live; scope K5 reservado rechaza | CPU exact distinto guard; sin crear archivos nativos |
| K4a-11 | Cuts A2..A7 de Open/Query/copy/close/free retienen fuerte; TRUE antes register no rescate | Fault hooks privados CPU; close/free attempts<=1; outcomes estables |
| K4a-12 | Poison de K1 bloquea identity/K2 y poison identity bloquea K1/K2 | Una única variable/lock y records fuertes; ningún healthy alias global |
| K4a-13 | Orden boundary/owner/session/context, registry corto, pin exige owner ya bloqueado; close/revoke/complete concurrentes; workspace L/n/B/r exacto en apéndice §4.3 | Barreras CPU causal; apéndice ROOT ratificado y regresión K1/K2 whole tras integración, sin relajar C2 |
| K4a-14 | Límite admissions4/threads8/pins2048/obs8192/subcalls229376; workspace SDK L131328/arena n131584/B512/requested132095/tail256; raw262656+SID136 separado | CPU positivo131584/512, negativos131328/8 y131328/512 antes allocate backend; cuotas borde+1/overflow calls0, un backing no doublecount; unknown retiene charge y tombstones no reciclan |
| K4a-15 | Cierre explícito handles reales una vez, pseudo nunca; free K1 base original una vez para arena/padding juntos; decremento(1,131584,132095) sólo tras reconocimiento completo | Doubles+query propia nativa normal tras ROOT release; free TRUE no reconocido retiene charge/poison; close repetido backend0, sin decremento doble; cortes inseguros sólo CPU |
| K4a-16 | Sanitización DTO/repr/exception sin SID/HANDLE/pointer/path/nonce/inputs del double | CPU sentinels, chaining suprimido; no leaks públicos |
| K4a-17 | Current own process normal: workspace131584/512/requested132095 compatible con K1, outputs sólo SDK131328; dos handles token, ID/group/stamp concordantes, cierre íntegro | Hijo Windows propio tras ROOT release; positivos base alineada y double con base4097→a4608/arithmetic §4.5, layout/tail separados; sin tokens de otro proceso, ACL/admin o files |
| K4a-18 | Poison/quota requieren retirada, no reboot registry ni SID nuevo en el proceso | CPU rechazo terminal; integración supervisor future evidencia terminate/reap propio |

Regresiones B01 específicas incluidas en K4a-04/06/13/14/15/17, todas futuras y sin relajar el contrato C2:

| Par causal futuro | Negativo / control positivo |
|---|---|
| Entrada allocator K1 |131328/B8 y131328/B512 rechazan ALIGNMENT_INVALID, allocate backend0;131584/B512 supera esos guards y conserva requested132095 |
| Metadata del pin | L/n/B/r/tail distinto, bool como int, arena/context ajeno o output fuera de tabla rechaza SDK calls0; nominal L131328/n131584/B512/r132095/tail256 pasa |
| Extensión de query | Fetch variable65537 o ReturnLength mayor que capacity rechaza sin resize/retry; capacity65536 y ReturnLength dentro del subbuffer permite parsing sólo de sus bytes reconocidos |
| SID contra tail | Pointer al otro subbuffer, a+131328 (primer byte del tail), a+131584 o margen externo rechaza; SID completo dentro de ReturnLength del subbuffer actual pasa |
| Overflow y dirección | Overflow al redondear L+B-1, n+B-1 o base+r rechaza/retiene según fase C2; helper con límite pequeño prueba el borde sin alloc real. Control b4097/a4608: intervalo n íntegro, tail256 y margen511 separados |
| Charge y cleanup | Carga `(1,131584,132095)` antes ENTRY, unknown la retiene íntegra; free/cierre conocido retira una vez; segundo close backend0/decremento0; tombstone unknown nunca libera cuota |
| Preimages y cuotas | Dos imágenes lógicas131328=262656, SID/group136 y un backing132095 suman394887 de payload solicitado; snapshot de n/r o sumarle otro backing rechaza en el double. Guards K1 count8/sum(n)8912896/sum(r)9437176 vigentes y borde+1 backend0 |

Las probes futuras sólo pueden observar tokens propios, usar ABI y memoria volátil K1 para buffers propios. No prueban archivos, ACL, admin, otros procesos, S1 full-chain, Docker/WSL, GPU o servicios. Un token válido no es evidencia de journal, store o M1. Coverage80 whole de módulos modificados y review/QA independientes quedan como gates de release, sin inventar porcentajes.

### 4.13 Fuentes primarias verificadas y versión de contenido

Consulta documental realizada el 2026-10-11. Se descargó sólo Markdown oficial en memoria para calcular tamaños/SHA256. No se instaló SDK ni se ejecutó código descargado.

Las firmas y derechos proceden de [OpenThreadToken](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openthreadtoken), [OpenProcessToken](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocesstoken) y [GetTokenInformation](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation). Las queries representan observaciones; el diseño de ratificación es una decisión propia.

Los campos de estado e identidad se apoyan en [TOKEN_STATISTICS](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_statistics), [TOKEN_PRIMARY_GROUP](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_primary_group) y [TOKEN_INFORMATION_CLASS](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-token_information_class). El cierre de handles se apoya en [CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle). ModifiedId cambia cuando cambia el token; su comparación no prueba trust de archivos.

También se verificaron [ERROR_NO_TOKEN=1008](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--1000-1299-), [ERROR_INSUFFICIENT_BUFFER=122](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-), [native thread ID](https://docs.python.org/3/library/threading.html#threading.get_native_id) y [ctypes LastError](https://docs.python.org/3/library/ctypes.html#ctypes.get_last_error). Native ID puede reutilizarse tras terminar el thread; la referencia retenida del thread es parte del record. Esas páginas complementarias se consultaron online; no se presentan como pins versionados de SDK.

Versión documental fijada: MicrosoftDocs/sdk-api commit `656e9656bfaef34dd29cd7ee9e1146aec17e924c`. Base: `https://raw.githubusercontent.com/MicrosoftDocs/sdk-api/656e9656bfaef34dd29cd7ee9e1146aec17e924c/sdk-api-src/content/`. No es una afirmación sobre un SDK instalado en el host.

| Ruta relativa sin .md | Bytes | SHA256 |
|---|---|---|
| processthreadsapi/nf-processthreadsapi-openthreadtoken | 5665 | 5fbdf4faaacaa8648713c3f9cffd511b78351082903e883f3a86a85fe8b5920b |
| processthreadsapi/nf-processthreadsapi-openprocesstoken | 5309 | 44b2292a4916704c79b513cf3dd3f3a39b7856b54303fb213b3388f4be097fd7 |
| securitybaseapi/nf-securitybaseapi-gettokeninformation | 6769 | c44e37ee00a0a4d8991ef840c7338dc763a8382f7773f659a990b705a67104c1 |
| winnt/ns-winnt-token_user | 3002 | 3073c9d2aa0786a6f53af86fafeda8293b32e03d901aec42be3dbadb090e8543 |
| winnt/ns-winnt-token_primary_group | 3413 | 1eb0ff36da1498089015da2deaca535582fbca701e47634d29fb961b7e4835ff |
| winnt/ns-winnt-token_statistics | 5089 | 65f638302c3c5764b5d979b5ecca86cbbb6567ec98c67b5ccffbfec645e7d492 |
| winnt/ne-winnt-token_information_class | 18602 | dac37af4909a1e44a3c558440e47ce9cdec5bb5530bb6ba808457224f01d9713 |
| winnt/ne-winnt-token_type | 3107 | f04afb049e85a0b1a2c9a559dc678ba0f183fb0d279a57b7965a50088d6c16dd |
| winnt/ns-winnt-sid_and_attributes | 2890 | a86b248c0e6f6ef604c23e1fcbb8b749b734651b37bc351837c88cf4b256a055 |
| handleapi/nf-handleapi-closehandle | 7266 | c0cd1b25e7d35a8f4fb020cfba13b9ee5b3643a332e7c1f592b507746e1e794b |
| processthreadsapi/nf-processthreadsapi-getcurrentprocess | 4681 | 7e15570b41fb44b9ed77685679afa4e7a8db91185182f0eb1bfc6b5a07b53b07 |
| processthreadsapi/nf-processthreadsapi-getcurrentthread | 4894 | a166536ec34673ed2b6dd83aaf224996c285b30b33b5b72264e463f6b3f6de1a |

## 5. Impacto en módulos y ficheros

| Ruta | Responsabilidad futura | Condición |
|---|---|---|
| `scripts/storage_journal_windows_identity.py` | Nuevo módulo identity: bootstrap privado, issuer/authority, policy/epoch, admission/pins, dobles CPU de tipos distintos | Declarado en brief; no existe ni se crea en esta pasada |
| `tests/test_storage_journal_windows_identity.py` | TDD futuro de origen nominal, queries, threads, revocación, custodia, caps/CPU negatives | Declarado en brief; no existe ni se crea en esta pasada |
| `scripts/storage_journal_windows_abi.py` | `_new_native_identity_backend`, dispatcher y layouts token cerrados §4.4/4.5 | Existe; permanece byte exacto |
| `scripts/storage_journal_windows_io.py` | Registry/latch/poison único, workspace pin y apéndice boundary→owner→session→context; K2 consume admission/pins | Existe K1; K2 futuro; permanece byte exacto |
| `tests/test_storage_journal_windows_io.py`, `tests/test_storage_journal_windows_abi.py` | Regresión/TDD de coordinación K1 y layouts/bindings del apéndice propuesto | Existen; permanecen byte exactos; ROOT debe declarar alcance futuro antes de modificar |
| `scripts/storage_journal.py` | Futuro seam privado `_bootstrap_journal_principal` del controller; codec U1 no adquiere authority por sus bytes | Existe; permanece byte exacto; wiring posterior a release ROOT |
| `scripts/storage_journal_windows.py` | U2 readonly y current_security_principal conservados; bytes no sirven como authority K4a | Existe; permanece byte exacto |
| `scripts/storage_receipt_store.py`, `scripts/storage_operator.py` | ReceiptLease/PublishedDiskBinding readonly sin promoción a emisor | Existen; permanecen byte exactos |
| `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-principal-design.md` | Destino canónico futuro de este contrato, decidido por ROOT tras selección/review/QA | No lo escribe este actor |

O2 queda descartada para emisión. El supervisor de retirada pertenece al lifecycle propio futuro; no emite authority K4a. El actor conserva ownership únicamente de este design.md.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| SID observado tomado como autorización | Posible | Crítico | Ratificación sólo en bootstrap confiable; authority nominal registrada, sin parámetro SID |
| Bucle de authority antes de query inicial | Posible | Bloqueante | Issuer con custodia mínima sólo de tokens propios; refresh no necesita pin K2 |
| Copy/pickle/nonce tratado como capability | Posible | Crítico | Exact type, registry identity, PID/provenance y vida actual; CPU separado; transporte O2 no concede authority |
| Impersonación o thread distinto | Posible | Crítico | Rechazo de cualquier token thread y pin nuevo en thread real de ENTRY |
| Token mutado entre checks | Posible | Crítico | TokenId/ModifiedId/primary group actuales; supuesto controller confiable explícito; ningún lock demuestra ausencia de ABA hostil |
| Interrupción post-TRUE | Posible | Crítico | Preregistro/custodia/poison; sin retry de open/close ni fake outcome |
| Epoch/S1 guard obsoleto | Posible | Crítico | Identidad y locks comunes; revocación de admission invalida dependientes; guard K4b actual obligatorio |
| Positive leaf usado contra MODIFY de ancestros | Ya observado | Crítico | Full-chain S1 continúa cerrada; no tocar ACL ni administración |
| Coordinación omitida o locks inversos | Posible | Crítico | Apéndice §4.3 explícito antes del RED; pin exige owner ya bloqueado, no toma boundary después; revoker no espera owner |
| Nueva doctrina inferida de O1 | Posible | Alto | S1/C2/O2 siguen vigentes; si ROOT exige otra frontera de amenaza, ADR separado |

## 7. Preguntas abiertas

| Puerta | Decisión/evidencia pendiente |
|---|---|
| Review/QA/adopción | Pendientes para este contrato seleccionado; estado aprobado registra elección y no aceptación técnica |
| Apéndice coordinación | ROOT ratifica §4.3 o declara cambio de decisión vía ADR. No liberar RED dependiente con locks indefinidos |
| Wiring runtime | ROOT libera la implementación concreta de seams §4.11 y su supervisor de retirada propio; no queda otro issuer por diseñar |
| Native release | ROOT autoriza probes tokens/memoria propios de §4.12; ninguna ejecución nativa hoy |
| ADR | n/a: propuesta concreta mecanismos privados dentro de S1/C2/O2 y ADR-0081. ROOT no autorizó escribir ADR/canon. Si el apéndice requiere revisar una decisión aceptada, propuesta ADR explícita antes de adopción |
| Autoridad de archivos | K3/K4b/K5/store y full-chain positiva siguen pendientes; ningún permiso nativo publicado por este documento |

Validación de entradas de esta pasada: 38 fuentes del snapshot comparadas contra `release-root.receipt.json`; 0 mismatches. SHA256 release: `515c8a831bbd94e14d98452c8c4af9d617e0545c71564515f9e2101bafef1b9d`. SHA256 contrato K2: `e41ab4860dbdd345cfede0bd32247bba4e08b9741e9272d54a63d9c416bfb7b9`. Los sellos prueban bytes, no autoridad nativa.

ROOT preservó la primera pasada22515 bytes/SHA256 `d2d0e6841bb0035540939949097d3e386cdd5ac8ae0ae550146e9ec4703c8e68` en `options-preserved-root.md`. `choice-root.receipt.json` fija O1 y libera esta segunda pasada; runtime_released=false y canonical_adoption=false.

La evidencia de esta pasada es documental. No se ejecutó Python, test, native query, SQL, DB, API, Docker/WSL, GPU, admin, ACL, instalación o servicio. El contrato seleccionado queda propuesto para revisión/QA/adopción ROOT; ningún archivo normativo o runtime fue editado por este actor.

FIX1 documental de B01, liberado por `release-root.receipt.json` a2026-10-11T20:25:28.516338+00:00 en el namespace privado `storage-journal-principal-k4a-contract-fix1-20261011`. Fuente inicial60443 bytes/SHA256 `24deb33ede18bfcf5058f759d3f1512c44b360eebf660f8f25fc3089d67ee135`; permanece byte exacta entre las41 entradas readonly de este snapshot. Antes de editar, verificación SHA256 de esas41 entradas:0 diferencias. El B01 Important completo se conserva en `prior-review.md`, incluida su prueba AST de prefijo real con backend0; esa prueba anterior no se presenta como prueba nativa ni ejecución de FIX1.

La elección ROOT de esta corrección conserva L131328, redondea n131584/B512 y solicita r132095; explicita tail256 y margen511. §4.1–4.9, las tablas SDK, cuotas/custodia, apéndice ROOT y matriz futura propagan esa distinción. C2 y su runtime no se modifican; revisión2/QA/adopción siguen pendientes. ADR-0084 permanece candidato privado ROOT de coordinación en otra entrada readonly: esta corrección no cambia doctrina S1/Constitución ni escribe un ADR. ROOT gestiona los medidores y la eventual adopción; el actor no reclama QA, probes nativas reales o release runtime.
