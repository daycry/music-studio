---
design: storage-journal-k2-acquisicion
titulo: Adquisición propia K2 con un owner por cadena candidata
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: spec.md
evaluacion: n/a
plan: improvement-plan.md
adr: n/a
opcion_elegida: O1
validada_por: ROOT bajo delegación vigente del propietario
validacion_utc: '2026-10-11T18:33:31.816708+00:00'
revision_documental: A/B intento1 conformes; QA1 119/119 controles documentales
adopcion_canonica: ROOT 2026-10-11T19:37:41.224496+00:00
implementacion: no liberada
canonical_target: docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-acquisition-design.md
enlaces_relativos_a: docs/roadmap/2026-09-28-m1-mvp-estudio
decision_base: ../../decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md
options_sha256: 398ce0f5deb5ff855df5095178aaeb968714059d44e1346d5b99fb060b64ab35
generacion:
  fuente: estimado
  medidor: ROOT
  tokens: null
  coste: null
  horas_ia: null
---

# Diseño — Adquisición propia K2 antes de emitir autoridad de producto

> Spec: [spec.md](spec.md), aprobada. Plan: [improvement-plan.md](improvement-plan.md). Base: [C2](storage-journal-kernel-design.md) y [ADR-0081](../../decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md).

| Dato | Valor |
|---|---|
| Opción elegida | O1, validada por ROOT el 2026-10-11 |
| Estado de la elección | Aprobado; revisión, QA y adopción documental pendientes |
| Autoría | Arquitecto; ROOT materializó y normalizó los retornos previos, sin atribuirse una transcripción literal |
| Alcance actual | Contrato documental; ningún RED, runtime, archivo nativo o gate de producto liberado |
| Colocación privada | `snapshot/docs/roadmap/2026-10-11-k2-acquisicion/design.md` por guardarraíl del rol |
| Colocación futura | `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-acquisition-design.md`, sólo tras adopción ROOT |

ROOT validará los enlaces desde la colocación futura M1. La colocación privada no cambia sus destinos normativos.

## 1. Contexto y restricciones

K2 adquiere handles propios y conserva todos los argumentos nativos desde antes de entrar hasta su reconocimiento completo. Sólo publica adquisiciones candidatas.

La [política S1](storage-nt-security-policy.md) exige principal ratificado antes de abrir candidatos. RootContext nace después de acreditar el ancla y todos los padres.

El orden obligatorio es K4a principal/admisión → K2 adquisición → K3 observación → K4b cadena S1 → K5 I/O → store. K4a no necesita RootContext ni cadena positiva.

K4a y K4b son fronteras del contrato previo K4. Su distinción elimina la dependencia circular; no ratifica un emisor por describirlo aquí.

[C2 §4.10](storage-journal-kernel-design.md) reserva K2–K5 y sus seams. El runtime K1 del snapshot es candidato corregido, con QA2 informada por ROOT y adopción todavía pendiente.

Por Constitución §2, K2 no accede a SQLite ni guarda datos fuera del proyecto. Preserva U1, U2 readonly, S1, G2 y la organización O2 de ADR-0081.

| Restricción | Consecuencia |
|---|---|
| Un owner por cadena candidata | Parent, leaf, locator y descriptor pertenecen al mismo registro y RLock |
| Tipo exacto y registro por referencia | Path, SID, hash, DTO, nonce público o flag no autentican capacidades |
| U2 aceptado readonly | `_ObservedHandle` no admite writer; K2 no importa su custodia o globals |
| Adquisición candidata | No entrega read/write, WriterLease, ChainLease, RootContext, geometry, store o ACK |
| CREATE NOREPLACE | FILE_CREATE/FILE_CREATED y descriptor cerrado; ningún OPEN_IF, overwrite o adopción |
| Incertidumbre | Revocación, poison del proceso y custodia hasta terminate/reap real; sin retry |
| Host actual con MODIFY outsider | S1 conserva SECURITY_UNACCREDITED; ningún leaf privado corrige sus ancestros |
| Gates nativos G1 | DIRECTORY/no-follow y ancla NTGUID requieren testigos propios aparte; sin fallback |

## 2. Opciones (2)

### O1 — Un owner para ancla, padres y leaf

La fachada conserva toda la candidata, sus cuotas, pins y llamadas en un registro. Cierra los hijos antes de sus padres.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: un lock de sesión y un protocolo de reconocimiento |
| Riesgo | Medio: un fallo revoca la candidata completa; las operaciones se serializan |
| Coste relativo | M |
| Reversibilidad | Alta antes de consumidores K3/K4; no introduce transferencias entre owners |

La fachada acredita ownership y completion. El módulo ABI prepara buffers propios y ejecuta firmas cerradas. K4b y el store futuros deciden confianza y ACK.

### O2 — Owner de directorios y owners de leaf con pins

Un owner conserva el prefijo. Cada leaf necesita otro owner y un pin nominal que impide cerrar prematuramente su parent.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: sesión, directorio y leaf mantienen locks y lifetimes distintos |
| Riesgo | Alto: ventanas de pin/unpin y cierre cruzado |
| Coste relativo | L |
| Reversibilidad | Media: exige retirar registros y pins entre owners |

La fachada coordina la cuota común y los tres niveles de locks. El backend ABI mantiene la misma receta nativa.

O2 permite conservar un prefijo al cambiar read/writer. Ese beneficio no elimina la exigencia S1 ni justifica sus transferencias para un único journal local.

## 3. Criterios de decisión

1. Registrar salida y argumentos antes de ENTRY pesa más que reutilizar un prefijo.
2. Un único lock debe cubrir adquisición, cierre y reconocimiento, incluidos los cortes después del retorno nativo.
3. La adquisición inicial debe existir antes de RootContext sin dar confianza por path.
4. La separación ABI/fachada C2 conserva import puro y dobles CPU sin ctypes.
5. Cuotas, tombstones y rotación deben impedir acumular owners antiguos sin límite.
6. Ninguna conveniencia de mínimos derechos, flush o provisión relaja S1.

## 4. Recomendación · opción elegida y por qué

**Recomendación y elegida: O1.** ROOT la seleccionó expresamente en `choice-root.receipt.json`, con fecha de validación del frontmatter.

O1 satisface los criterios 1, 2 y 5 mediante un owner único. Mantiene K4a antes del ancla y K4b después de las observaciones.

O2 se descarta por sus transferencias y cierres cruzados. Su reutilización del prefijo no compensa esas ventanas en el controller local actual.

### 4.1 Tipos opacos y factories exactas

Todas estas operaciones son privadas de `scripts/storage_journal_windows_io.py`. Sus capabilities no se serializan ni tienen constructor público útil.

| Firma cerrada | Precondición y resultado |
|---|---|
| `_new_native_acquisition_owner(admission: _AcquisitionAdmission) -> _AcquisitionOwner` | Admisión nativa viva registrada por K4a, mismo pid; gate Windows x64 y binding completo. Sin backend, SID, path o flags del caller. |
| `_assemble_cpu_acquisition_owner(ops: _AcquisitionOps, *, principal_sid: bytes, primary_group_sid: bytes) -> _AcquisitionOwner` | Assembly privada de tests; SIDs sintácticamente válidos, provenance fija `cpu_double`. No emite admisión nativa. |
| `_locate_anchor(owner: _AcquisitionOwner, *, project_location: str) -> _AnchorLocator` | Owner vivo; localización cerrada §4.5. Sólo navegación registrada. |
| `_open_owned_anchor(owner: _AcquisitionOwner, locator: _AnchorLocator) -> _OwnedAcquisition` | Locator propio vivo; ANCHOR_CANDIDATE, OPEN_EXISTING, parent nulo, descriptor nulo. |
| `_open_owned_component(owner: _AcquisitionOwner, parent: _OwnedAcquisition, name: str, profile: _AcquireProfile, disposition: _Disposition, descriptor: _ClosedDescriptor-or-None) -> _OwnedAcquisition` | Parent directorio candidato propio; tabla §4.3 y guard CREATE §4.2. |
| `_new_closed_descriptor(owner: _AcquisitionOwner, *, role: _NewObjectRole) -> _ClosedDescriptor` | Construcción cerrada §4.6; capability registrada antes de retornar. |
| `_acquisition_info(owner: _AcquisitionOwner, acquisition: _OwnedAcquisition) -> AcquisitionInfo` | Registro propio; devuelve copia sin HANDLE, path, SID o nonce. |
| `_close_acquisition(owner: _AcquisitionOwner, acquisition: _OwnedAcquisition) -> AcquisitionCloseOutcome` | Cierre explícito §4.11; también admite propias revoked/closed/unknown. |
| `_close_acquisition_owner(owner: _AcquisitionOwner) -> AcquisitionCloseOutcome` | Revoca sesión y cierra en postorden; outcome agregado estable. |

`_AcquisitionOwner`, `_OwnedAcquisition`, `_AnchorLocator` y `_ClosedDescriptor` usan slots y factories internas. No implementan conversión a int, buffer protocol, copy o pickle con autoridad.

La validación exige `type(x) is ExpectedType`, pertenencia al registro y referencia `is`. Rechaza subclass, duck typing y `object.__new__` sin entrada auténtica.

No admite `_MemoryContext`, AlignedArena, `_ObservedHandle`, ReceiptLease, WriterLease o RootContext como sustitutos. El mismo proceso sigue siendo código confiable; esto no promete sandbox frente a Python hostil interno.

### 4.2 Admisión previa, scopes y guard de creación

`_AcquisitionAdmission` pertenece al emisor K4a. K2 sólo consume su entrada nominal registrada y revalida su estado bajo el protocolo de locks.

| Campo privado del admission record | Tipo y condición exacta |
|---|---|
| `capability`, `issuer_ref` | Objetos opacos exactos; issuer registrado y vivo, nunca ID suministrado |
| `pid` | int exacto igual al pid actual; no PID de un launcher supuesto |
| `scope` | Enum interno `_AdmissionScope`, §tabla siguiente |
| `principal_sid`, `primary_group_sid` | bytes exactos, SID revision1, 1..15 subauthorities, longitud exacta 8+4*n, máximo68 |
| `principal_ratification_ref` | Capability privada del deployer actual; bytes de SID aislados no la reemplazan |
| `effective_context_ref` | Contexto observado actual; impersonación no ratificada rechaza |
| `source` | Literal interno `native_windows_x64`; inmutable y contrastado con issuer, no argumento del caller |
| `policy_ref`, `epoch_ref` | Objetos de política y epoch registrados, vivos, referidos por identidad |
| `state` | `live/revoked/unknown/closed`; sólo live autoriza construir owner |

El seam requerido de K4a será `_issue_acquisition_admission(deployer_authority, *, scope: _AdmissionScope) -> _AcquisitionAdmission`. Recibe DeployerAuthority nominal, nunca un SID/path/config/flag autoritativo.

K4a debe concretar y revisar su emisor, token efectivo, ratificación e impersonación antes de su propio RED y release nativo K2. Este documento cierra el contrato consumidor, sin implementar o ratificar ese emisor.

Cada frontera backend requiere `_pin_current_acquisition_admission(admission, *, owner) -> _AdmissionPin`, seam consumidor K4a nominal. No basta consultar un estado cached sin revalidar contexto efectivo actual.

`_AdmissionPin` guarda admission_ref, owner_ref, pid actual, thread_id actual, principal/group actuales, policy_ref, epoch_ref y state live. Su registro K4a debe acreditar origen y vigencia por referencia.

Principal/group/policy/epoch deben coincidir con el owner, sin conversión de un DTO en pin. Impersonación no ratificada o cambio bloquean antes de ENTRY con PRINCIPAL_UNACCREDITED.

El call record retiene el pin hasta reconocer cada frontera. K4a debe fijar su consulta efectiva y revocación antes de su RED; K2 no inventa el emisor desde el nombre del seam.

| Scope nominal | Profiles permitidos y frontera |
|---|---|
| `CANDIDATE_READ_ONLY` | ANCHOR_CANDIDATE, PARENT_EXISTING, READ_EXISTING; ningún creator/writer |
| `PRODUCT_CHAIN_CANDIDATE` | Todos los profiles de §4.3, pero CREATE exige guard parent S1 actual de K4b |
| `OWNED_PROBE_CANDIDATE` | Reservado al emisor/testigo propio K5; K2 actual rechaza su uso nativo no liberado con ADMISSION_REQUIRED |

Scope describe adquisición potencial. Ninguno emite authority de store, I/O, RootContext o ACK.

Sin emisor K4a liberado, `_new_native_acquisition_owner` rechaza ADMISSION_REQUIRED antes de cargar DLLs o llamar backend. Un assembly CPU nunca satisface ese precheck.

CREATE consulta `owner.admitted_parents` por referencia exacta. K4b debe haber emitido `_ParentS1Admission` para ese parent, rol de hijo, cadena actual y el mismo principal/epoch.

| Campo del guard K4b consumido por K2 | Condición |
|---|---|
| `owner_ref`, `parent_ref`, `admission_ref` | Referencias auténticas registradas; mismo owner y principal |
| `child_role` | FILE_JOURNAL para CREATE_FILE; DIRECTORY_DOMAIN para CREATE_DIRECTORY |
| `chain_ref`, `observation_epoch_ref`, `policy_ref` | Cadena completa S1 admitida por K4b; actual y retenida bajo owner lock |
| `state`, `source` | `live`, `native_windows_x64`; nada de flags suministrados por caller |

Revocación de parent, admisión, cadena o epoch invalida el guard antes de ENTRY. Los creator access profiles sólo abren candidatos existentes y nunca emiten ese guard.

Tests CPU usan `_seed_cpu_parent_admission(owner,parent,*,role) -> None`, assembly privada que registra `_CpuParentAdmission` de tipo distinto. Sólo acepta owner `cpu_double` y adquisiciones CPU del mismo registro.

Ese seed permite probar la rama mecánica CREATE con dobles. No fabrica `_ParentS1Admission`, RootContext, ChainLease ni adquisición nativa, y no puede entrar por una factory de producción.

### 4.3 Profiles, máscaras, shares y dispositions

Los enums son nominales internos. No usan IntEnum ni aceptan str/int equivalentes, generic access o máscaras calculadas por caller.

| `_AcquireProfile` | Access | Share | CreateOptions | `_Disposition` | Descriptor |
|---|---|---|---|---|---|
| ANCHOR_CANDIDATE | `0x001200A0` | `3` | `0x00200021` | OPEN_EXISTING | None; sólo `_open_owned_anchor` |
| PARENT_EXISTING | `0x001200A0` | `3` | `0x00200021` | OPEN_EXISTING | None |
| PARENT_CREATE_FILE | `0x001200A2` | `3` | `0x00200021` | OPEN_EXISTING | None |
| PARENT_CREATE_DOMAIN | `0x001200A6` | `3` | `0x00200021` | OPEN_EXISTING | None |
| READ_EXISTING | `0x00120081` | `1` | `0x00200068` | OPEN_EXISTING | None |
| WRITER_EXISTING | `0x00120083` | `0` | `0x0020006A` | OPEN_EXISTING | None |
| CREATE_FILE | `0x00120083` | `0` | `0x0020006A` | CREATE_NEW | Propio FILE_JOURNAL |
| CREATE_DIRECTORY | `0x001200A6` | `3` | `0x00200021` | CREATE_NEW | Propio DIRECTORY_DOMAIN |

`OPEN_EXISTING` fija Nt FILE_OPEN=1 e Information FILE_OPENED=1. `CREATE_NEW` fija Nt FILE_CREATE=2 e Information FILE_CREATED=2. Mismatch rechaza antes de ENTRY.

| Grupo | Bits específicos cerrados |
|---|---|
| Padres | TRAVERSE `0x20`, READ_ATTRIBUTES `0x80`, READ_CONTROL `0x20000`, SYNCHRONIZE `0x100000` |
| Parent creador | ADD_FILE `0x2`; ADD_SUBDIRECTORY `0x4` sólo en PARENT_CREATE_DOMAIN/CREATE_DIRECTORY |
| Archivo read | READ_DATA `0x1`, READ_ATTRIBUTES, READ_CONTROL, SYNCHRONIZE |
| Archivo writer | Archivo read + WRITE_DATA `0x2` |
| Directory options | DIRECTORY `0x1`, SYNCHRONOUS_IO_NONALERT `0x20`, OPEN_REPARSE_POINT `0x200000` |
| File read options | NON_DIRECTORY `0x40`, NONALERT `0x20`, NO_INTERMEDIATE_BUFFERING `0x8`, OPEN_REPARSE_POINT `0x200000` |
| File writer options | File read options + WRITE_THROUGH `0x2` |
| Shares | SHARE_READ `0x1`, SHARE_WRITE `0x2`; nunca SHARE_DELETE `0x4` |

Excluye GENERIC, MAXIMUM_ALLOWED, APPEND_DATA, DELETE, WRITE_DAC, WRITE_OWNER, backup intent, inheritable handle y DELETE_ON_CLOSE. No añade rights para hacer pasar flush o lifecycle.

NtCreateFile recibe AllocationSize=NULL y EA=NULL/0. FileAttributes=0 en OPEN; NORMAL `0x80` en CREATE_FILE; DIRECTORY `0x10` en CREATE_DIRECTORY.

OA.Attributes fija únicamente OBJ_CASE_INSENSITIVE `0x40`; SecurityQualityOfService=NULL. No copia OBJ_KERNEL_HANDLE o flags kernel-only a user-mode.

G1 debe acreditar `0x00200021` sobre directorios propios. La documentación enumera compatibles sin OPEN_REPARSE_POINT y también explica no-follow; K2 no resuelve esa tensión por inferencia.

Ese gate pendiente impide atribuir éxito nativo de producto a la receta. No convierte un futuro SUCCESS/OPENED íntegro en fallo de completion por faltar la evidencia documental del gate.

### 4.4 ABI y bindings completos antes de recursos

La factory nativa sólo carga tras admission y el gate C2: Windows AMD64, punteros de8 bytes y Python de64 bits. ARM64, 32bits o plataforma ambigua rechazan.

`scripts/storage_journal_windows_abi.py` conserva import sin ctypes/DLL. `_new_native_acquisition_backend() -> _AcquisitionOps` importa ctypes y fija todas las firmas de esta sección.

Usa DLLs del sistema `ntdll`, `kernel32` y `advapi32`, WinDLL con `use_last_error=True`. Símbolo o layout distinto produce ABI_UNACCREDITED antes de recursos K2.

| Tipo x64 | Layout y tamaño obligatorio |
|---|---|
| HANDLE, PVOID, PSID, PACL, PWSTR | Pointer8; `c_void_p` o puntero a WCHAR16 retenido, nunca conversión automática de strings |
| NTSTATUS, BOOL, WELL_KNOWN_SID_TYPE | `c_int32`,4 |
| DWORD, ULONG, ACCESS_MASK, UINT | `c_uint32`,4 |
| UCHAR, USHORT, WCHAR | `c_uint8`1, `c_uint16`2, `c_uint16`2 |
| SIZE_T, ULONG_PTR | `c_size_t`,8 |
| LARGE_INTEGER | `c_int64`,8; AllocationSizeNULL en K2 |
| UNICODE_STRING | Length:u16@0, MaximumLength:u16@2, Buffer:pointer@8; size16/align8 |
| OBJECT_ATTRIBUTES | Length:u32@0, RootDirectory:pointer@8, ObjectName:pointer@16, Attributes:u32@24, SD:pointer@32, SQOS:pointer@40; size48/align8 |
| IO_STATUS_BLOCK | Unión Status:i32/Pointer:pointer@0 de8; Information:size_t@8; size16/align8 |
| SECURITY_DESCRIPTOR absoluto | Revision:u8@0, Sbz1:u8@1, Control:u16@2, Owner:pointer@8, Group:pointer@16, Sacl:pointer@24, Dacl:pointer@32; size40/align8 |
| ACL | Revision:u8@0,Sbz1:u8@1,AclSize:u16@2,AceCount:u16@4,Sbz2:u16@6; size8/align2; buffer base múltiplo4 |
| ACE_HEADER | Type:u8@0,Flags:u8@1,Size:u16@2; size4/align2 |
| ACCESS_ALLOWED_ACE fijo | Header@0,Mask:u32@4,SidStart:u32@8; size12/align4; extensión variable `8+sid_length` |
| SID binario | Revision:u8@0,SubAuthorityCount:u8@1,IdentifierAuthority:6 bytes@2,SubAuthority:u32[n]@8; length `8+4*n`,1..15 |

Sin `_pack_` artificial. Los offsets se verifican con las estructuras nativas propias; no importa structs U2 para acreditar estos layouts.

Abreviaturas de firmas: P=pointer8, W=pointer a WCHAR16, U=u32, I=i32, H=HANDLE8, B=BOOL/i32, S=u16. `T*` indica salida sobre storage retenido.

| DLL / función | argtypes → restype; receta fija |
|---|---|
| ntdll / NtCreateFile | `(H*,U,OBJECT_ATTRIBUTES*,IO_STATUS_BLOCK*,LARGE_INTEGER*,U,U,U,U,P,U)->I`; once argumentos de §4.3 |
| kernel32 / CloseHandle | `(H)->B`; una llamada por adquisición; error inmediato ante FALSE |
| kernel32 / GetVolumePathNameW | `(W,W,U)->B`; capacidad salida32768 WCHAR |
| kernel32 / GetVolumeNameForVolumeMountPointW | `(W,W,U)->B`; capacidad50 WCHAR, root DOS terminado en barra |
| kernel32 / QueryDosDeviceW | `(W,W,U)->U`; capacidad32768 WCHAR; nombre sin trailing barra |
| kernel32 / GetDriveTypeW | `(W)->U`; sólo DRIVE_FIXED=3 aceptado por locator |
| advapi32 / CreateWellKnownSid | `(I,P,P,U*)->B`; kinds22 y26, DomainSidNULL, capacidad68 |
| advapi32 / IsValidSid | `(P)->B`; sólo SID en buffer propio; FALSE no usa error residual |
| advapi32 / GetLengthSid | `(P)->U`; sólo tras IsValidSidTRUE; debe igualar longitud binaria calculada |
| advapi32 / InitializeSecurityDescriptor | `(P,U)->B`; revision1 |
| advapi32 / InitializeAcl | `(P,U,U)->B`; longitud ACL exacta y ACL_REVISION2 |
| advapi32 / AddAccessAllowedAce | `(P,U,U,P)->B`; revision2, mask específica, SID propio; función sin flags heredables |
| advapi32 / SetSecurityDescriptorOwner | `(P,P,B)->B`; SID principal, OwnerDefaultedFALSE |
| advapi32 / SetSecurityDescriptorGroup | `(P,P,B)->B`; primary group observado, GroupDefaultedFALSE |
| advapi32 / SetSecurityDescriptorDacl | `(P,B,P,B)->B`; presentTRUE, ACL noNULL, DefaultedFALSE |
| advapi32 / SetSecurityDescriptorControl | `(P,S,S)->B`; interest/value SE_DACL_PROTECTED=`0x1000` |
| advapi32 / IsValidSecurityDescriptor | `(P)->B`; FALSE → DESCRIPTOR_INVALID, sin pointer externo |
| advapi32 / GetSecurityDescriptorControl | `(P,S*,U*)->B`; control y revision desde storage propio |
| advapi32 / GetSecurityDescriptorOwner | `(P,P*,B*)->B`; verifica pointer SID dentro del rango propio y defaultedFALSE |
| advapi32 / GetSecurityDescriptorGroup | `(P,P*,B*)->B`; misma regla sobre group |
| advapi32 / GetSecurityDescriptorDacl | `(P,B*,P*,B*)->B`; presentTRUE, defaultedFALSE y pointer ACL propia |

Los helpers BOOL de construcción/consulta capturan last_error inmediatamente ante FALSE. Los predicados IsValidSid/IsValidSecurityDescriptor no atribuyen un last_error residual a un FALSE.

Sólo el binder nativo normaliza un BOOL firmado32 a bool exacto mediante comparación con cero. No usa bool/truthiness sobre resultados del double o un objeto del caller.

GetDriveTypeW retorna un enum; 0/1 o cualquier valor distinto3 rechaza ANCHOR_UNACCREDITED, sin inventar GetLastError. QueryDosDeviceW=0 captura error inmediato.

La factory no devuelve DLLs, pointers o `call(name,*args)`. `_AcquisitionOps(open,close,locate,descriptor)` es frozen, de tipo exacto y sólo assembly privada.

| Seam backend interno | Resultado exacto y restricción |
|---|---|
| `open(call: _AcquisitionCallFrame) -> _NativeCreateCompletion` | Frame registrado propio; sólo NtCreateFile con tabla fija. HANDLE queda en slot propio, nunca en DTO. |
| `close(call: _AcquisitionCallFrame) -> _NativeCloseCompletion` | Sólo el HANDLE actual del record, una vez; devuelve bool exacto/errornullable. |
| `locate(call: _AcquisitionCallFrame) -> _LocatorCompletion` | Secuencia SDK cerrada §4.5; cada subllamada se registra antes de ENTRY. |
| `descriptor(call: _AcquisitionCallFrame) -> _DescriptorCompletion` | Secuencia SDK cerrada §4.6; no SetSecurityInfo/ACL de objetos existentes. |

`_NativeCreateCompletion(return_status:int,iosb_status:int,information:int,iosb_unchanged:bool)` es privado y frozen. NTSTATUS se normaliza a u32; Information a u64; tipos exactos, sin coerción del caller.

`iosb_unchanged` compara los16 bytes con su preimagen; no sustituye la lectura del slot retenido. Ambos statuses/Information deben coincidir con ese storage bajo lock.

`_NativeCloseCompletion(success:bool,win32_error:int-or-None)` sólo usa bool exacto; éxito exige errorNone. `_LocatorCompletion` y `_DescriptorCompletion` sólo contienen `success:bool,diagnostic:AcquisitionDiagnostic-or-None`; los datos quedan en arenas propias.

Un close FALSE exige win32_error u32 capturado, incluido0 válido; None significa captura incompleta y produce unknown. Helper success exige diagnosticNone; helper failure exige diagnóstico exacto correspondiente.

Un double con resultado distinto al tipo exacto o fields inválidos produce RESOURCE_UNKNOWN. No se normaliza un None, número truthy o objeto con conversión.

### 4.5 Locator y adquisición del ancla sin parent

`project_location` es navegación no autoritativa. K2 admite sólo str exacto DOS absoluto `X:\` seguido de componentes validados, sin UNC, prefijos NT/extended, slash, dotsegments o NUL.

Límite de entrada:16383 unidades UTF16, sin NUL; input buffer máximo32768 bytes con terminador. Esta cota interna permite la salida SDK32768WCHAR dentro de la cuota por llamada.

El locator no acepta una letra como credencial. Usa esa letra para localizar un candidato que K3/K4 deberán acreditar por handle.

| Paso SDK, sin retry | Validación exacta |
|---|---|
| 1. GetVolumePathNameW del input DOS | TRUE, UTF16 estricto terminado dentro de32768; root exactamente `X:\` del input, comparación letra case-insensitive; otro root/mount-folder rechaza |
| 2. GetDriveTypeW del root | Resultado3; red, removible u otro tipo rechaza este perfil cerrado |
| 3. GetVolumeNameForVolumeMountPointW | TRUE; exactamente `\\?\Volume{8-4-4-4-12 hex}\`,49 WCHAR antesNUL; capacidad50, terminación comprobada |
| 4. QueryDosDeviceW de `X:` y de `Volume{GUID}` | Cada retorno1..32768; MULTI_SZ dentro del count, exactamente un target; target `\Device\HarddiskVolume` +1..20 dígitos ASCII; igualdad exacta de ambos targets |
| 5. Repetir las dos queries como observaciones posteriores | Segundo par idéntico al primero; no son reintentos de fallos; ningún cambio/ambigüedad se admite |
| 6. Registrar locator | Copia propia de rootDOS, GUID, target y NTname; sin SID personal/path de usuario en DTO |

Una salida de GetVolumePathNameW puede seguir junctions o ignorar sufijos inválidos. Sus resultados sólo localizan; no demuestran existencia, ausencia de reparse ni confianza de componentes.

El NTname interno se ensambla como `\??\Volume{GUID}\`. No usa el ObjectName absoluto del caller. Su sintaxis y binding operativo quedan en G1, con testigo exacto aparte.

`_AnchorLocatorRecord` guarda capability, owner_ref, rootDOS, GUID, target, NTname, source, state y arena_refs. La capacidad registrada no se puede crear desde un DTO/hash.

El NTname genérico admite como máximo32766 WCHAR/65532 bytes más NUL. La receta GUID actual ocupa49 WCHAR/98 bytes y NUL2,100 bytes de buffer; nunca rebasa USHORT.

`_open_owned_anchor` fija RootDirectory=NULL. Registra el output como cualquier componente, con ANCHOR_CANDIDATE y FILE_OPEN/OPENED; §4.9 sigue íntegra.

El resultado es `_OwnedAcquisition` candidata, con `parent_ref=None`. No se aplica excepción TrustedInstaller ni se construye RootContext por el GUID.

K3 futuro consulta identidad, tipo, volumen, path canónico y metadata del mismo handle. K4b compara esos datos actuales con locator, contexto deployer y el root real del sistema Windows.

K4b obtiene el contexto Windows mediante su contrato propio, incluido GetSystemWindowsDirectoryW y handles reales. No infiere system-root desde el locator, una letra o una variable de entorno.

Después adquiere root→proyecto→data→_storage por un componente retenido cada vez. Sólo tras S1 de todos esos handles emite RootContext/ChainLease.

### 4.6 Descriptor nuevo: owner, GROUP, DACL y buffers

`_NewObjectRole` tiene sólo FILE_JOURNAL y DIRECTORY_DOMAIN. Sus masks son respectivamente `0x00120083` y `0x001200A6`.

Owner=principal ratificado. GROUP=primary group observado explícitamente; ese campo no agrega trustees ni grants a la allowlist.

CreateWellKnownSid obtiene SYSTEM/kind22 y Administrators/kind26 en buffers propios68. IsValidSid y GetLengthSid verifican ambos y su igualdad con los SIDs well-known exactos.

Deduplica por bytes en orden principal, SYSTEM si distinto y Administrators si distinto. Emite1..3 ALLOW explícitos, flags0, misma mask específica por role.

No prohíbe principal SYSTEM/Admin. No agrega DENY, ACE heredables, GENERIC, CREATOR_OWNER, OWNER_RIGHTS, SACL o SID personal embebido.

| Orden SDK de construcción, cada paso registrado | Comprobación |
|---|---|
| InitializeSecurityDescriptor(revision1) | TRUE; SD absoluto propio40 bytes |
| InitializeAcl(length,revision2) | TRUE; length=`8+sum(8+sid_length)` y <=236 |
| AddAccessAllowedAce por SID deduplicado | TRUE; orden fijo, masks específicas, flags0 |
| SetSecurityDescriptorOwner/Group | TRUE; ambos DefaultedFALSE |
| SetSecurityDescriptorDacl | TRUE; presentTRUE, noNULL, DefaultedFALSE |
| SetSecurityDescriptorControl | TRUE; protected `0x1000` |
| IsValidSecurityDescriptor y getters de §4.4 | TRUE; revision1, control exacto `0x1004`, SaclNULL, owner/group/ACL propios |

Comprueba bytes ACL: revision2, Sbz1/Sbz2=0, size exacto, AceCount deduplicado y ACE lengths/masks/SIDs/flags exactos. No reordena un descriptor existente.

Las APIs owner/group/DACL referencian buffers. `_ClosedDescriptorRecord` retiene SD/ACL y los SID ranges del control arena hasta cierre del owner o cuarentena.

Getters exigen pointer igual a la base exacta del SID/ACL previsto, además de rango íntegro propio. Un pointer distinto nunca se dereferencia; resultado incongruente tras ENTRY es RESOURCE_UNKNOWN.

Todas las subllamadas completan antes de publicar `_ClosedDescriptor`. Fallo BOOL conocido devuelve DESCRIPTOR_INVALID con error inmediato y ningún NtCreateFile.

No llama SetNamedSecurityInfo, SetSecurityInfo, SetFileSecurity o un servicio. Crear cerrado no endurece objetos preexistentes; K3/K4 releerán el descriptor por handle.

### 4.7 Nombres, UTF16 y arenas de llamada

El validator puro de componente copia la semántica U2 sin importar su custodia. K2 exige str exacto, no vacío, distinto`.`/`..`, y UTF16LE estricto<=510 bytes.

Rechaza controles<32, caracteres `\\/:*?"<>|`, trailingdot/space y stems reservados antes del primer punto: CON,PRN,AUX,NUL,CONIN$,CONOUT$,COM/LPT1..9 y¹²³.

La sintaxis no acredita ausencia de alias8.3. K3/K4 mantienen canonical name/identity por handle y rechazo de reparse.

`_CallArena` es storage propio con layout cerrado. Native usa un único array de UCHAR para cada bloque; overlays ctypes sólo referencian ese backing.

No crea temporales SDK mediante c_wchar_p, create_unicode_buffer, create_string_buffer, from_buffer_copy o arrays fuera del ledger de arenas. CPU usa storage del double, jamás dereferencia addresses ficticios.

Cada segmento se alinea a8 bytes, o a su alineación menor acreditada. El layout suma segmentos con overflow validado, redondea a8 y solicita `n+7` para alinear la base.

La cuota carga `requested=n+7`, incluido todo padding interno y externo. Checks previos aseguran `0<requested<=131072` y rangos dentro del backing; no pasa pointer del caller.

UNICODE_STRING.Length excluye NUL; MaximumLength=Length+2. OA.Length=48; output HANDLE inicialNULL. IOSB inicia unión=`0x000000007FFFFFFF`, Information=`0xFFFFFFFFFFFFFFFF`.

### 4.8 Registros, cuotas, slots y rotación

| Registro fuerte | Campos/lifetime |
|---|---|
| `_LIVE_ACQUISITION_OWNERS` | Owner exacto, pid, admission_ref, backend, source, state, RLock, control arena y counters; antes de recursos |
| `owner.acquisitions` | Capability/record por referencia; slot_index, parent_ref, profile, disposition, descriptor_ref, completion, state, child_pins, outcome |
| `owner.locators`, `owner.descriptors` | Objetos exactos, record, source, state y backing refs propios; no weakrefs |
| `owner.admitted_parents` | Guards K4b referidos por identidad; CPU guards de tipo distinto no pasan native |
| `owner.inflight` | `_AcquisitionCallRecord` con operation, phase, record_ref, all_args, backing refs, output/IOSB refs, charge, parent pin, return y preimágenes |
| `_QUARANTINED_ACQUISITION_OWNERS` | Owner/calls/backends/arenas/records inciertos fuertes hasta terminate/reap real |
| `_CLOSED_ACQUISITION_OWNERS` | Tombstones de owners cerrados, máximo4 por proceso; sin backing nativo ni HANDLE operativo |

| Enum privado | Valores exactos |
|---|---|
| `_OwnerState` | building,live,revoked,closing,closed,unknown |
| `_AcquisitionState` | reserved,entered,candidate,revoked,closing,closed,failed,unknown; failed es tombstone no publicado de un fallo conocido |
| `_CallPhase` | reserved,entered,returned,completed,acknowledging,acknowledged,unknown |
| `_AuxiliaryState` | building,live,revoked,closed,unknown; para descriptor/locator |
| `_Disposition` | OPEN_EXISTING,CREATE_NEW |
| `_NewObjectRole` | FILE_JOURNAL,DIRECTORY_DOMAIN |
| `_SegmentName` | control,principal_sid,group_sid,system_sid,admin_sid,project_input,root_input,guid_input,device_input,utf16_output,unicode_name,unicode_string,object_attributes,absolute_sd,dacl,sdk_outputs; plan fijo de la operación, sin nombres del caller |

Los enums privados no son inputs str/IntEnum. Los DTO sólo copian sus nombres; owner.info no entrega estados internos reserved/entered/building como capacidad.

| Estructura privada Python | Campos tipados cerrados |
|---|---|
| `_AcquisitionRecord` | capability:_OwnedAcquisition,owner_ref:_AcquisitionOwner,slot_index:int[0..255],parent_ref:_OwnedAcquisition-or-None,profile:_AcquireProfile,disposition:_Disposition,descriptor_ref:_ClosedDescriptor-or-None,completion:_NativeCreateCompletion-or-None,state:_AcquisitionState,child_pins:int[0..63],outcome:AcquisitionCloseOutcome-or-None,native_close_attempted:bool,diagnostic:AcquisitionDiagnostic-or-None |
| `_AcquisitionCallFrame` | owner_ref:_AcquisitionOwner,operation:closed enum §4.12,record_ref:_AcquisitionRecord-or-None,arena_refs:tuple[_CallArena,...],admission_pin:_AdmissionPin-or-CPU-only pin,parent_ref:_OwnedAcquisition-or-None,profile:_AcquireProfile-or-None,disposition:_Disposition-or-None,descriptor_ref:_ClosedDescriptor-or-None,locator_ref:_AnchorLocator-or-None,slot_index:int-or-None,phase:_CallPhase |
| `_AcquisitionCallRecord` | frame:_AcquisitionCallFrame,charge:tuple[count:int,requested:int,handle:int],preimage:private snapshot exacto,return_value:uno de los cuatro resultados backend exactos-or-None,primary:AcquisitionDiagnostic-or-None,cleanup:AcquisitionCloseOutcome-or-None,subcalls:list[_SdkCallRecord] |
| `_SdkCallRecord` | function:enum de las funciones SDK de §4.4,ordinal:int,phase:_CallPhase,arena_refs:tuple[_CallArena,...],output_ranges:tuple[(arena_ref,offset:int,length:int),...],preimage:bytes,return_scalar:int-or-None,win32_error:u32-or-None |
| `_CallArena` / record | owner_ref,backing_ref fuerte,logical_length:int,requested_bytes:int,aligned_offset:int[0..7],segments:tuple[(name:enum,offset:int,length:int,alignment:int),...],state:_AuxiliaryState; sin pointer público |

El pin CPU es `_CpuAdmissionPin(owner_ref,pid:int,thread_id:int,state:_AuxiliaryState)` emitido sólo por el assembly CPU. No es `_AdmissionPin` y nunca autentica `_new_native_acquisition_owner`.

El plan de subllamadas es el orden fijo de §4.5/4.6. Ordinal es posición dentro de ese plan, sin selección de función o argumentos por caller.

Los rangos son locales y validados mediante resta antes de ENTRY. Campos None sólo corresponden a su operación; una combinación incompatible rechaza pre-entry.

El snapshot de preimagen contiene state/outcome/pins/counters, lista de inflight y referencias fuertes de backings. No guarda texto arbitrario de exceptions como diagnóstico.

El control arena preasigna256 slots únicos y sus outputs antes de la primera NtCreateFile. Nunca recicla un índice, tampoco tras un fallo terminal conocido.

| Rango del control arena lógico10240 bytes | Elementos exactos |
|---|---|
| 0..2047 | HANDLE[256],8 bytes cada uno |
| 2048..6143 | IOSB[256],16 bytes cada uno |
| 6144..7167 | ReturnStatus U32[256] |
| 7168..8191 | Close BOOL[256] |
| 8192..9215 | CloseError U32[256] |
| 9216..9487 | Cuatro SID ranges de68: principal,group,SYSTEM,Administrators |
| 9488..9503 | Cuatro SID length U32 |
| 9504..9563 | Salidas SDK: present BOOL@9504,PACL@9512,defaulted BOOL@9520,owner PSID@9528,ownerdefault BOOL@9536,group PSID@9544,groupdefault BOOL@9552,control USHORT@9556,revision DWORD@9560 |
| 9564..9575 | SDK BOOL@9564, error U32@9568, DWORD result@9572 |
| 9576..10239 | Reserva cero; no bytes SDK ocultos |

Su solicitud es10247 bytes (`10240+7`). Sus overlays no agregan backing; todos sus rangos quedan cargados a quota desde el registro owner.

| Cuota O1 | Regla cerrada |
|---|---|
| Handles cargados | <=64; live, reserved, pending y unknown, incluidas anclas y todos los padres |
| Records/slot indices | <=256 intentos registrados durante toda sesión, incluidos failed/closed tombstones; contador monotónico |
| Descriptors | <=8, cada backing requested<=4096; incluyen SD, ACL y padding propios; SID refs ya cargadas al control arena |
| Locators | <=4, cada backing requested<=65534; includes NTname/root/GUID/target/padding propios |
| Arena pool | <=8 backings presentes/reserved/retained, cada requested<=131072, suma<=1048576 por owner |
| Call frame | <=1 entered por owner; suma de requested de backings distintos referidos por ese frame<=131072 |
| Owners por proceso | <=4 registros emitidos en toda vida del proceso, contando live/closed/unknown; contador nunca decrementa |

Control, descriptors y locators consumen el mismo arena pool. Sus máximos individuales no prometen que todos sean alcanzables simultáneamente.

Cada backing se carga una sola vez al aggregate. Un frame que lo referencia lo cuenta una sola vez en su propio límite131072, sin duplicar el aggregate.

Ejemplo de locator: control10247 +input32775 +salida65543 =108565 bytes solicitados. Los helpers reutilizan esa salida sólo después de reconocer completamente cada subllamada.

No agrega un buffer SDK de salida65536 fuera del ledger ni lo confunde con capacidad WCHAR. Descriptor/locator nuevos rechazan si falta pool o cuota, antes de llamar SDK.

K2 no usa AlignedArena ni `_allocate_aligned`. Sus metadata buffers cuentan aquí; las arenas I/O alineadas K1 mantienen count/logical/requested y registro K1 independientes.

Un consumidor K3/K5 que necesite una arena K1 deberá pinnear su capability auténtica y cargarla al ledger K1. No podrá ocultar ese backing como metadata K2.

DTO/copias Python y overhead de objetos no son buffers SDK adicionales. Estas cuotas miden backing solicitado declarado; no son una cota física OS, reserva virtual real o memoria total Python.

Antes de ENTRY se carga cada handle, slot y backing. Known failure/close acreditado devuelve sólo sus cargas retornables; unknown conserva todas.

Los tombstones no se evictan. No reutiliza un scalar antiguo como credencial; un valor numérico reciclado por Windows sólo vale por una nueva acquisition registrada y completada.

Agotar records o arenas devuelve ACQUISITION_LIMIT/calls0. El caller cierra sanamente la sesión y reacredita en otro owner; no hereda handles/guards.

Tras cuatro owners emitidos se exige rotación normal del proceso, incluso si todos cerraron. No limpia el contador para admitir un quinto owner ni conserva owners viejos ilimitados.

El supervisor futuro debe terminar/reap y comprobar salida real antes de liberar cuarentena o reemplazar el proceso. Su contrato/QA pertenece a rotación/lifecycle posterior; K2 no ejecuta ese supervisor.

### 4.9 Adquisición: registrar output antes de publicar

| Frontera | Acción obligatoria bajo owner lock |
|---|---|
| A0 precheck | Tipos, PID, admission, global poison, profile/disposition/descriptor, parent, scope, nombres y cuotas. Fallo: calls0. |
| A1 reserva | Capability interna aún no retornable; record reserved, índice monotónico, charge handle, pin parent y arenas. |
| A2 pre-entry | Slot=NULL, IOSB sentinel; call record/all args/output refs fuertes insertados. Cada SDK helper también tiene subrecord previo. |
| A3 entered | Phase entered registrada antes de la llamada NtCreateFile; ninguna referencia sale de custodia. |
| A4 retorno | Binder registra statuses/Information y comparación preimagen; fachada contrasta frame y storage propios. |
| A5 completion | Valida §4.10; guarda completion íntegra y HANDLE propio acreditado en record, aún sin retorno al caller. |
| A6 reconocimiento | Construye capability/DTO internos, actualiza accounting/pins/inflight de éxito; mantiene preimágenes fuertes hasta finalizar. |
| A7 publicación | Únicamente tras A6 completo state=candidate y capability retornable. Ningún scalar o pointer sale. |

El binder escribe el HANDLE en el slot preregistrado. El registro conserva esa célula aunque un corte impida copiar el scalar después del retorno.

No expone `_NativeCreateCompletion`, `_AcquisitionCallFrame`, _AcquisitionOps o un slot al store/caller. El resultado de open es sólo capability candidata propia.

Interrupción entre A3 y reconocimiento completo, incluido éxito antes del registro, produce unknown/poison. No rescata el output copiándolo retrospectivamente para cerrar.

Error ordinario propio después de A5 íntegro permite rollback con CloseHandle una sola vez. Preserva causa primaria; cleanup unknown queda separado.

Un BaseException, completion parcial o duda sobre registro no permite ese rollback. Retiene owner/frame/output/SD/backend y exige retiro del proceso.

### 4.10 Estados terminales, IOSB y errores

El éxito exige retorno STATUS_SUCCESS=0, IOSB.Status=0 e Information exacta1/2 según disposition. No acepta NT_SUCCESS genérico, warning, pending o un status positivo distinto0.

El HANDLE del slot debe ser int exacto nativo en1..`2^64-1`, distinto INVALID_HANDLE_VALUE=`2^64-1` y pseudohandles conocidos `-1..-6` normalizados a u64.

Esa validación escalar no autentica handles externos. Sólo vale sobre el output de la llamada propia reconocida, con el record reservado anterior.

También exige que el scalar no esté en otro record live/entered/closing/unknown del owner. Una colisión con otro handle retenido es RESOURCE_UNKNOWN, sin segundo close sobre ese scalar.

| Retorno/slots | Clasificación y acción |
|---|---|
| SUCCESS0 +IOSB0 +Information esperada +HANDLE propio válido | Completion acreditada; aún exige A6/A7 antes de publicar |
| STATUS_PENDING=`0x103` | RESOURCE_UNKNOWN, process poison/custody; sin wait/cancel/retry |
| Warning/informational/nonzero fuera de error severidad3 | RESOURCE_UNKNOWN; ningún NT_SUCCESS shortcut |
| Error severidad3 (`0xC0000000..0xFFFFFFFF`) +outputNULL +IOSB íntegramente sentinel | Fallo terminal conocido; IOSB sin escribir no se presenta como status leído exitoso |
| Mismo error +outputNULL +IOSB.Status igual al retorno e Information0 | Fallo terminal conocido con IOSB escrito; unión high32=0 |
| Error +output noNULL, IOSB distinto, escritura parcial o info diferente | RESOURCE_UNKNOWN; nunca CloseHandle sobre scalar no acreditado |
| SUCCESS con outputNULL/invalid, IOSB sentinel o info incorrecta | RESOURCE_UNKNOWN; no capacidad |
| Exception/interrupción entered, wrapper inválido o mismatch wrapper/storage | RESOURCE_UNKNOWN; strong retention y retiro |
| Validation/SDK fallo conocido antes NtCreateFile | Diagnóstico cerrado, sin file acquisition; devuelve las cargas acreditadas |

En error conocido libera la carga provisional de handle y call buffers ya completados. Conserva el slot/tombstone monotónico sin authority ni retry de esa llamada.

Ese resultado no promete ausencia del nombre ni ausencia de efectos parciales OS. Un CREATE fallido no autoriza adoptar, borrar o reintentar un objeto por path.

| NTSTATUS conocido | Código de adquisición |
|---|---|
| `0xC0000035` STATUS_OBJECT_NAME_COLLISION en CREATE | CONFLICT; conserva el objeto existente |
| `0xC0000034` NAME_NOT_FOUND / `0xC000003A` PATH_NOT_FOUND en OPEN | NOT_FOUND; no CREATE fallback |
| `0xC0000043` SHARING_VIOLATION | SHARING_CONFLICT; no reintento con shares nuevos |
| `0xC0000022` ACCESS_DENIED | ACCESS_DENIED; no activar privilegios ni ampliar access |
| Otro error terminal conocido | OPEN_FAILED; status u32 sanitizado, sin mensaje del sistema |

Los valores numéricos anteriores se contrastaron con [Microsoft MS-ERREF: NTSTATUS Values](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55). Su clasificación operativa conservadora pertenece a este contrato.

NtCreateFile no produce un Win32 error997 en este seam. Si un helper BOOL entregara ERROR_IO_PENDING=997, completion incierta → RESOURCE_UNKNOWN; no tratarlo como fallo ordinario liberable.

### 4.11 Close, rollback, locks y postorden

Orden de locks: guardia global localiza/pinnea owner y se suelta; después owner.RLock. Revalida exacttype/PID/state y `_KERNEL_POISONED` compartido con K1.

La mutación global bajo owner lock no espera otro owner lock. Ningún camino mantiene global mientras espera RLock. No usa GIL como ownership lock.

Cada operación del owner se serializa, incluida subllamada SDK y reconocimiento. No ejecuta logging extensible, callbacks del caller o lifecycle bajo ese lock.

Parent y child pertenecen al mismo owner. A1 pinnea parent antes de ENTRY; success mantiene pin hasta cierre conocido del child; unknown conserva pin hasta retiro.

Un parent close con children pinneados revoca nuevas adquisiciones y autoridad futura de su subárbol. Rechaza CAPABILITY_IN_USE/calls0; no reserva un intento nativo de close.

Después de cerrar los children acreditadamente, un close explícito puede cerrar ese parent. No es retry nativo: el precheck anterior no llamó CloseHandle.

| Ventana de close | Regla |
|---|---|
| C0 | Reserva AcquisitionCloseOutcome unknown y revoca capacidad antes de cualquier llamada. Guarda preimágenes de record/pins/quotas/inflight y refs. |
| C1 | Preregistra frame de close con slot propio y salidas BOOL/error; fija native_attempted antes de CloseHandle. |
| C2 | CloseHandle exacto una sola vez; wrapper bool/error se reconoce contra outputs del frame. |
| C3 | TRUE completado: construye tombstone y outcome, contabiliza cargas y retira inflight; todavía conserva preimágenes. |
| C4 | Sólo tras C3 íntegro publica closed, clears authority y libera backing retornable. Ésta es la frontera de reconocimiento completo. |
| Corte C1–C3 o cualquier interrupción antes C4 completo | Outcome unknown estable, poison global y custodia conservadora; rollback de accounting/pins necesarios para retención; no repetir CloseHandle. |
| FALSE, 997, invalid wrapper, exception o TRUE con reconocimiento incompleto | Misma salida unknown; error primario y cleanup separados. |
| Close repetido después del primer intento entered | Devuelve outcome reservado/final; native calls total<=1. |

No publica closed después de TRUE antes de completar constructor/accounting/inflight. Otro thread sólo observa tras el RLock y recibe unknown si ese reconocimiento fue interrumpido.

Closed completo anterior se conserva aunque una operación distinta falle después. Una interrupción del caller después del retorno completo no convierte una llamada nueva en el primer close.

Para rollback de adquisición se aplica el mismo protocolo. CloseTRUE seguido de corte queda unknown/free1/retry0; jamás se trata como recurso aún operativo.

`_close_acquisition_owner` reserva unknown agregado y revoca todo antes de cerrar. Visita records en índice decreciente, omite closed y falla si la relación parent/child no respeta índice ascendente.

Ese orden es postorden porque el parent siempre se registró antes del child. Conserva todas las anclas hasta cerrar sus descendientes.

El primer close unknown detiene llamadas restantes; el poison impide frees/closes adicionales. Records restantes quedan revoked y retenidos; closed previos mantienen su outcome.

Si todos cierran y el reconocimiento agregado termina, owner pasa closed. Invalida descriptors/locators, borra authority nativa y devuelve exactamente las cargas reconocidas.

Un context manager, destructor, atexit o GC no puede declarar cleanup. K2 exige cierre explícito, con primaria y cleanup separados.

La custodia de backing heap sólo se suelta tras completion y bookkeeping acreditados. Ante incertidumbre mantiene referencias; no llama VirtualFree ni reintenta liberar buffers K1.

### 4.12 DTO, códigos y sanitización

| DTO frozen exacto | Campos y enums |
|---|---|
| `AcquisitionInfo` | `profile:str, disposition:str, state:str, provenance:str`; copies de nombres internos; state candidate/revoked/closed/unknown; provenance native_windows_x64/cpu_double |
| `AcquisitionDiagnostic` | `code:str, operation:str, win32_error:int-or-None, ntstatus:int-or-None`; numéricos exactos u32, sin bool |
| `AcquisitionCloseOutcome` | `state:str, causes:tuple[AcquisitionDiagnostic,...]`; state closed/unknown; causas ordenadas e inmutables |
| `AcquisitionError` | Exception con diagnostic exacto y cleanup outcome opcional; str sólo `code/operation`, `from None` |

Operaciones cerradas: `owner,locate,descriptor,open_anchor,open_component,info,close,owner_close`. Profile/disposition en DTO son observación, no enums de entrada reutilizables.

| Code | Operaciones permitidas |
|---|---|
| PLATFORM_UNSUPPORTED, ABI_UNACCREDITED | owner |
| ADMISSION_REQUIRED, PRINCIPAL_UNACCREDITED | owner,locate,descriptor,open_anchor,open_component |
| SECURITY_UNACCREDITED | open_component; guard K4b CREATE inválido |
| CAPABILITY_INVALID, OWNER_MISMATCH, CAPABILITY_REVOKED | todas |
| CAPABILITY_IN_USE | close |
| PROFILE_INVALID, DISPOSITION_INVALID | open_component |
| DESCRIPTOR_INVALID | descriptor,open_component |
| COMPONENT_INVALID | locate,open_component |
| ANCHOR_UNACCREDITED | locate,open_anchor |
| ACQUISITION_LIMIT | owner,locate,descriptor,open_anchor,open_component |
| OPEN_FAILED,NOT_FOUND,CONFLICT,SHARING_CONFLICT,ACCESS_DENIED | open_anchor,open_component; CONFLICT sólo CREATE |
| RESOURCE_UNKNOWN, OWNER_RETIRE_REQUIRED | todas salvo info; info observa unknown sin llamada |

El constructor valida code/operation y rangos. Rechaza enum desconocido, subclass, números bool y causas mutables.

La causa primaria siempre queda primera. Un cleanup unknown no afirma que la operación principal no ocurrió y nunca reemplaza esa causa.

DTO/error/repr no contienen path, SID, usuario, HANDLE, addresses, nonce, GUID o texto arbitrario de exceptions/doubles. No retiene el mensaje secreto como diagnóstico.

### 4.13 Matriz antes de RED y límites de evidencia

| ID | Control causal requerido | Evidencia y límite |
|---|---|---|
| K2-01 | Exacttypes, object.__new__, subclass, copy, deserializado, crossowner/PID/admission/provenance | CPU; todos rechazos pre-entry calls0 |
| K2-02 | Tabla completa access/share/options/disposition y descriptorNULL/role | CPU compara argumentos capturados; no sharing Windows acreditado |
| K2-03 | UTF16 astral/unpaired/NUL/control/devices/superscripts/510B/trailing y locator bound | CPU; no canonical alias metadata |
| K2-04 | SD owner/GROUP/dedup SYSTEM/Admin, masks, flags, control/layout/getterranges | CPU seam; testigo SD nativo liberado aparte |
| K2-05 | Anchor parentNULL, locator registrado/forged/stale y sequence SDK count/terminators/mount/SUBST | CPU; NTGUID/no-follow G1 real posterior |
| K2-06 | Pre-entry slot/IOSB/refs/pins/charge visibles al double | CPU; ninguna acquisition creada por caller |
| K2-07 | SUCCESS0/IOSB0/OPENED1 o CREATED2 solamente; todos mismatches | CPU negativo; no producto |
| K2-08 | ErrorNULL con IOSB unchanged vs escrito exacto vs parcial; collision/missing/sharing/access | CPU; no claim ausencia/cleanup de nombres |
| K2-09 | PENDING/warning/invaliddouble/exception y processwide poison K1+K2 | CPU; nuevos owners calls0, strong custody |
| K2-10 | Cortes A1..A7 y después nativeSUCCESS antes ack/registro/publicación | CPU; never-close unknown, retiro requerido |
| K2-11 | Ordinary register failure tras completion vs BaseException; primary/cleanup | CPU; close único sólo en rama acreditada |
| K2-12 | Cortes tras CloseTRUE en constructor/accounting/inflight hasta C4 | CPU; unknown estable/free1/retry0, no closed temprano |
| K2-13 | Parent pins, parent close rival, owner postorden y primer unknown | Threads CPU; ningún GIL shortcut |
| K2-14 | Todos máximos, requested padding, shared backing uniquecount, pending/retained y tombstones | CPU; cuotas solicitadas, no físicas |
| K2-15 | Cuatro owners totales, cierre sano/rotación/reap y no eviction | CPU de contrato; supervisor nativo futuro propio |
| K2-16 | DTO/error/repr con sentinels secretos del double | CPU; sin pointers/texto interno |
| K2-17 | Binding/layout de todas las structs y SDK signatures | ABI CPU fixture; no Windows nativo fingido |
| K2-18 | Apertura relativa, sharing bilateral, descriptor alCREATE y no-follow exactos | Windows propio sólo tras release ROOT; no ACL/admin de ancestros existentes |

Este documento no ejecutó esos tests. TDD n/a: prosa; cada cambio runtime futuro requiere RED causal, review, cobertura y QA reales según dev-cycle.

### 4.14 Fuentes Microsoft y pins de contenido

Se consultaron fuentes primarias el 2026-10-11. Las tablas de contrato propias concretan un perfil más limitado; una página API no acredita el host ni un gate.

| Grupo de hechos | Fuente directa |
|---|---|
| NtCreateFile, ancla absoluta/relativa, output/IOSB, shares/disposition/options | [NtCreateFile user-mode](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile), [WDK](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile), [OBJECT_ATTRIBUTES](https://learn.microsoft.com/en-us/windows/win32/api/ntdef/ns-ntdef-_object_attributes) |
| Localización, salida y límites SDK | [GetVolumePathNameW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumepathnamew), [GetVolumeNameForVolumeMountPointW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumenameforvolumemountpointw), [QueryDosDeviceW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-querydosdevicew), [GetDriveTypeW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getdrivetypew) |
| SID types/helpers | [WELL_KNOWN_SID_TYPE](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-well_known_sid_type), [CreateWellKnownSid](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-createwellknownsid), [IsValidSid](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-isvalidsid), [GetLengthSid](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-getlengthsid) |
| SD/ACL/ACE structures | [SECURITY_DESCRIPTOR](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-security_descriptor), [ACL](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-acl), [ACCESS_ALLOWED_ACE](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-access_allowed_ace) |
| Construcción SD/ACL | [InitializeSecurityDescriptor](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-initializesecuritydescriptor), [InitializeAcl](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-initializeacl), [AddAccessAllowedAce](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-addaccessallowedace) |
| Componentes SD | [SetOwner](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-setsecuritydescriptorowner), [SetGroup](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-setsecuritydescriptorgroup), [SetDacl](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-setsecuritydescriptordacl), [SetControl](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-setsecuritydescriptorcontrol) |
| Validación/getters SD | [IsValid](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-isvalidsecuritydescriptor), [GetControl](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-getsecuritydescriptorcontrol), [GetOwner](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-getsecuritydescriptorowner), [GetGroup](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-getsecuritydescriptorgroup), [GetDacl](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-getsecuritydescriptordacl) |

Pins byte exactos del repositorio oficial MicrosoftDocs/sdk-api: commit `656e9656bfaef34dd29cd7ee9e1146aec17e924c`. Base raw: `https://raw.githubusercontent.com/MicrosoftDocs/sdk-api/656e9656bfaef34dd29cd7ee9e1146aec17e924c/sdk-api-src/content/`.

Cada ruta siguiente añade `.md` a esa base. El arquitecto descargó exclusivamente Markdown en memoria y calculó SHA256; no instaló ni ejecutó binaries.

| Ruta relativa sin .md | Bytes | SHA256 |
|---|---|---|
| winternl/nf-winternl-ntcreatefile | 37266 | d35698185fa62bd5d819a78b7f0f4b5161e6211fae1a461fdbde8a673d29469e |
| ntdef/ns-ntdef-_object_attributes | 9482 | 469e85fd85408f9849039237683c4d7b7ceccd27187b81bc9bad36a2961975ba |
| securitybaseapi/nf-securitybaseapi-setsecuritydescriptordacl | 7142 | 3a0a0a5b787307410da441850ce4b714dac276e1a49be055859e181c96a67c4c |
| fileapi/nf-fileapi-getvolumenameforvolumemountpointw | 5903 | beb557ce2e77b194d5a814bb50d1c7c52c8a5aa3a8567c7bdf07c9f05b815e8d |
| securitybaseapi/nf-securitybaseapi-createwellknownsid | 3230 | 49831e0626585dd0f9c3ec2df8aa51e9f00a50c385266672c113bcacf2d18942 |
| securitybaseapi/nf-securitybaseapi-isvalidsid | 3517 | 524cb3ff989392ee716bb8d28b2ed7cfc20a4cec146dc19802b954bf79ae6cd8 |
| securitybaseapi/nf-securitybaseapi-getlengthsid | 3097 | 002b2767af9afd3598f157d644bc09381a371fb9d7bf2718f01a48c5e66a2156 |
| securitybaseapi/nf-securitybaseapi-initializesecuritydescriptor | 5286 | b9e6ee6efe4d3add09a63473f333d705c9982e48dc543a218016fb550a0519a3 |
| securitybaseapi/nf-securitybaseapi-initializeacl | 8028 | 8026a18f728a3cddc64820e283b12ca7650eebc2b094b97762720623ed6d2922 |
| securitybaseapi/nf-securitybaseapi-addaccessallowedace | 6274 | fe28e33f6ec2c89565748a53dc047036b34fe1f3f92c526e79063995bc859c1c |
| securitybaseapi/nf-securitybaseapi-setsecuritydescriptorowner | 4853 | a6452d4120d4b97f566aafe7ce1c134bb8f948c3c30ff98ceee8a952743e487d |
| securitybaseapi/nf-securitybaseapi-setsecuritydescriptorgroup | 4805 | ab4747d132803a8428ba2d6c8e4443bbadd48c07d2ffee3e5ef247ce139d5e3f |
| securitybaseapi/nf-securitybaseapi-setsecuritydescriptorcontrol | 4650 | f5914f15691f6ab40ff64cdba9f7f9d3ec11776aa001ed2d6755f23e2dc29f81 |
| securitybaseapi/nf-securitybaseapi-getsecuritydescriptorcontrol | 4194 | ae94e6b5c59927b22887d1efd3820dc88ab06b947a9603d54ad6edae3e9684c9 |
| securitybaseapi/nf-securitybaseapi-getsecuritydescriptorowner | 4853 | 32413b23857cf3525f32b51e05e0c9ee9d6878c2a1e2c830e81eb4583ede21cd |
| securitybaseapi/nf-securitybaseapi-getsecuritydescriptorgroup | 4891 | 8a8b4c0f3b68ed3c22e92055f92e76b9181f0833ea29e52bc7c7066122688371 |
| securitybaseapi/nf-securitybaseapi-getsecuritydescriptordacl | 6134 | 59a92ed76479c6b3a26f2c9fdb10ac96cbcd4b5a1d246c591446034321aa8cdf |
| securitybaseapi/nf-securitybaseapi-isvalidsecuritydescriptor | 4834 | f8c35fd0cabf575a77441e5070756cd965897f695615be3f8eb28e2ea134c9ca |
| fileapi/nf-fileapi-getvolumepathnamew | 9388 | 01fed4d7877806c7fb25fc649f924517988d7c0e58373b1827d1a77773979fb2 |
| fileapi/nf-fileapi-querydosdevicew | 7188 | 845316324ced6964bfb44ec63be5ba4e01d4c40b95350f50672b5fd975519c9c |
| fileapi/nf-fileapi-getdrivetypew | 5367 | 17da0a984f0754bd447f89698bc395cd04c6a802b0f43384dd3f69270101d5fb |
| winnt/ne-winnt-well_known_sid_type | 27622 | 4cb5883142d2467ed42d86da5a07cd9246f13449f365157433fd87ea24b7fd61 |
| winnt/ns-winnt-security_descriptor | 4901 | aee9b8b18d20ec96255d8978929a5b4999b4dd029d8415d9f6aec298ba7891ed |
| winnt/ns-winnt-acl | 5114 | 5b60734a4a546943ae8b5e5432ea7c2d58a6b145f77e756f368dc94f5372deca |
| winnt/ns-winnt-access_allowed_ace | 5067 | 547b8e508748a01f64ea1124e930c41fc881236fb93f0be88127095a44822260 |

## 5. Impacto en módulos y ficheros

| Ruta real | Cambio futuro O1 | Estado de esta pasada |
|---|---|---|
| `scripts/storage_journal_windows_io.py` | Owner/admission consumer, acquisition/arenas/slots/quotas/close privados; conserva K1 | Readonly snapshot; sin código |
| `scripts/storage_journal_windows_abi.py` | Backend K2 tardío, layouts/helpers cerrados, native outputs propios | Readonly snapshot; sin código |
| `tests/test_storage_journal_windows_io.py` | Controles CPU y cortes causales K2-01..16 | Readonly snapshot; sin tests |
| `tests/test_storage_journal_windows_abi.py` | Layout/binding y seams K2-17 | Readonly snapshot; sin tests |
| `scripts/storage_journal_windows.py` | U2 permanece readonly; no importar sus globals/capabilities | Conservado |
| `scripts/storage_journal.py` | U1 codec no cambia | Conservado |
| `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-acquisition-design.md` | Destino documental declarado por ROOT | Sólo mapeo futuro; no escritura canónica |

Los actores futuros reciben ownership explícito de cada release. Este documento no descompone tareas, horas o presupuesto.

No nace un ADR nuevo: O1 concreta custody dentro de C2/O2 sin cambiar doctrina previa. `adr: n/a` refiere esa ausencia, no revoca ADR-0081 ni S1.

Si K4a, G1, flush o lifecycle requieren cambiar una decisión aceptada, ROOT deberá promover una propuesta de ADR aparte. No se reserva número aquí.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación verificable |
|---|---|---|---|
| Native success antes del registro | Media | Crítico | Slot/arena/call preregistrados; cortes A3..A7 → poison/custody/no close |
| TRUE close publicado antes de accounting | Media | Crítico | C3 íntegro antes C4; cortes de constructor/accounting/inflight → unknown/free1/retry0 |
| Creator access tomado como trust | Media | Crítico | Guard `_ParentS1Admission` actual de K4b requerido por identidad |
| Locator/SID como credencial | Media | Crítico | K4a nominal previo, locator sólo navegación, K4b única emisión RootContext |
| No-follow DIRECTORY/NTGUID asumidos | Media | Alto | G1 exacto nativo aparte, sin fallback; separar completion de evidencia de producto |
| MODIFY outsider en host | Alta según evidencia previa | Alto | S1 SECURITY_UNACCREDITED; ningún ACL/admin/provision incluido |
| SDK buffers fuera de cuota | Media | Alto | Backings únicos del pool, offsets cerrados, K2-14 y ningún buffer ctypes implícito |
| Tombstones/owners acumulados | Media | Alto | 256 slots y cuatro owners monotónicos; rotación/reap separado obligatorio |
| Parent close concurrente | Media | Alto | Pin antes ENTRY, RLock único y postorden; subtree revocation |
| Flush exige rights extra | Pendiente de testigo | Alto | Gate ADR-0081/K5; no GENERIC_WRITE silencioso ni cambio de buffering |

## 7. Preguntas abiertas

No quedan campos, perfiles, enums, layouts, quotas, classifications o calling seams internos K2 por inferir.

| Gate futuro de otra unidad | Condición de release pendiente |
|---|---|
| K1 dependencia | ROOT debe adoptar runtime tras sus gates actuales; QA2 verde no es adopción implícita |
| K4a issuer | Contrato de token/ratificación/impersonación/emisor nominal cerrado y revisado antes de su RED y K2 nativo |
| G1 testigos | DIRECTORY `0x00200021`, apertura relativa y ancla NTGUID exactos; Windows propio liberado aparte |
| K3 observación | Queries metadata/mode/streams/G2 propias, nunca WriterLease→ObservedHandle |
| K4b full-chain | Ancla/system-root y S1 de toda cadena, guards parent CREATE actuales; host todavía no positivo |
| K5 probe/I/O | Scope propio distinto y read/write/flush exactos; minimum rights/flush witness sin ampliación silenciosa |
| Rotación/lifecycle | Supervisor terminate/reap real y reacreditación; no fakefree o limpieza de registry para continuar |
| Store/recuperación/aceptación | ST/ACK/bootstrap/lifecycle/recovery/ext4/E2E/manuales siguen obligatorios |

T05/M1 permanecen abiertos. La elección y esta concreción no liberan implementación, gates nativos o autoridad de producto.

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-11 | Opciones O1/O2; ROOT eligió O1 y ratificó clarificaciones; contrato K2 candidato escrito sólo en design.md autorizado |


## Acta ROOT de adopción documental — 2026-10-11T19:37:41.224496+00:00

ROOT autentica313payloads,34inputs,107imports y herramientas fijadas;28pinsprivados/27guardascanónicas sin cambio. Revisión1 A/B sin gaps; QA documental119/119 y gatesledger/coverage/qa0. Se adopta el contrato O1 como concreción de ADR0081/C2; ninguna implementación ni autoridad nativa se concede por este acto. El cuerpo describe el corte histórico del arquitecto: K1 actualmente está aceptado y publicado en ddc509b, por encima del estado candidato citado en ese corte. Metadata anterior de elección se preserva y sólo revisión/adopción se actualizan.

El informe QA fue escrito directamente por su actor en la ruta nueva autorizada; no se afirma un CAS ROOT anterior de dicho informe. PDF disponible sólo local, inspección first/last HTMLprintpreview; sin rasterización de sus páginas. T05/M1 abiertos y K4aissuer/principal/pin/G1real/K3/K4b/K5/rotación/store/ACK/recovery/bootstrap/lifecycle/ext4/E2E/manuales pendientes. Nada de RootContext/fullchain por prosa. Uso realnull.


## Coordinación candidata K4a — ADR0084 propuesta

Apéndice normativo candidato para revisión; no incorporado al runtime existente. [Contrato principal](storage-journal-principal-design.md) y [decisión propuesta](../../decisiones/ADR-0084-frontera-nativa-y-admision-del-principal-windows.md) condicionan su adopción. Prefijo histórico íntegro. Fuente3c20d078, extracciónbyteexacta del diseño seleccionadoO1; elecciónno grantnativo niK1actualconforme automáticamente.

Esta subsección propone la coordinación necesaria para integrar K4a. No modifica bytes canónicos ni afirma que el runtime K1 actual ya la implemente. ROOT deberá ratificarla como concreción antes del RED que dependa de ella.

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


Ratificación documental ROOT (2026-10-11T20:45:39.188502+00:00): el apéndice K4a y ADR0084 quedan aceptados tras revisión2 y QA232/232. La nota candidata anterior conserva el estado histórico de la propuesta. Su implementación y la comprobación actual del código quedan pendientes.
