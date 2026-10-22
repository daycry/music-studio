---
design: storage-journal-store-windows
titulo: Contrato del store nativo Windows y ACK del journal M1 T05
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: spec.md
evaluacion: n/a
plan: improvement-plan.md
adr: ../../decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md
opcion_elegida: O2
validada_por: ROOT bajo delegación vigente del propietario
validada_utc: '2026-10-11T14:39:03.061125+00:00'
revision_documental: aceptada; revisión2 A/B y QA95checks
implementacion: no liberada
canonical_target: docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md
canonical_adr_target: docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md
decisiones_fijadas: ADR-0075/O2, ADR-0076/S1, ADR-0078/G2
generacion:
  fuente: estimado
  medidor: ROOT
  tokens: null
  coste: null
  horas_ia: null
---

# Diseño — Contrato del store nativo Windows y ACK del journal

> Spec M1 aprobada. ROOT eligió organización O2 bajo delegación el 2026-10-11. Revisión2 A/B y QA documental aprobadas; ROOT incorpora el contrato. El código y los experimentos requieren liberación por unidad.

| Campo | Valor |
|---|---|
| Estado | Organización O2 aprobada e incorporada por ROOT tras revisión2 y QA documental |
| Opción elegida | O2: kernel I/O privado y store separados |
| Validación | Las decisiones durable O2, seguridad S1 y geometría G2 permanecen fijadas |
| Evidencia propia | Lectura de fuentes y Microsoft Learn; sin I/O experimental, admin, Git, GPU o cambios canónicos |

Los enlaces de esta copia se resuelven desde los destinos canónicos previstos: `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md` y `docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md`. ROOT adopta estos documentos tras revisión2 y QA95checks; ADR-0081 queda aceptado. La implementación nativa aún no está liberada.

## 1. Contexto y restricciones

ADR-0075 exige journal estable, PREPARE/COMMIT, CAS, intención antes del efecto y resultado antes de éxito. ADR-0076 exige toda la cadena S1. ADR-0078 aporta geometría readonly G2; B candidato no es capacidad de writer.

`scripts/storage_journal.py` implementa U1: cabecera, 64 slots, snapshots exactos, inspección y decisiones puras. `scripts/storage_journal_windows.py` implementa observación U2a/U2b y cierre con custodia. Ninguno implementa el store o un ACK durable. El contrato conserva ambos alcances aceptados.

`ReceiptLease` en `scripts/storage_receipt_store.py` y `PublishedDiskBinding` en `scripts/storage_operator.py` conservan su API readonly. El controller futuro elimina los writers JSON por ruta de `storage_offline.py`, `storage_publish.py` y `storage_attach.py`, después de revisión y QA de su wiring.

La Constitución mantiene todo dentro del proyecto y SQLite de producto sólo en el server. El journal registra infraestructura. No abre BD, invoca engines o modifica pesos. Los componentes de esta propuesta corren en Windows x64 user-mode y sólo admiten NTFS local acreditado.

La entrada autoritativa son las 17 fuentes readonly del snapshot de `release-root.receipt.json`. Los módulos auxiliares existentes se consultaron para sus firmas, no como evidencia de store aceptado. Una actualización del ledger canónico por ROOT no cambia el snapshot.

## 2. Opciones (3)

Las tres organizaciones entregan el mismo store, ACK, clasificación de recovery y gates físicos. O1–O3 sólo identifican organización interna; no reabren O2 de ADR-0075.

| Opción | Organización concreta | Complejidad | Riesgo | Coste relativo | Reversibilidad |
|---|---|---|---|---|---|
| O1 | Integrar adquisición writable, trust, arenas e I/O en `scripts/storage_journal_windows.py`; codec separado | Alta: concentra observación y store | Medio-alto: amplía superficie de regresión U2 | S: menos fronteras internas, mismos tests NT | Media: rollback debe separar cambios readonly |
| O2, elegida | `scripts/storage_journal_windows_io.py` para kernel privado; `scripts/storage_journal_store.py` para trust/CAS/ACK | Alta: fronteras nominales y custodia explícita | Medio: preserva adquisiciones readonly aceptadas | M: verificar ownership entre módulos | Alta: módulos nuevos se retiran conservando U1/U2/historial |
| O3 | Proceso propio propietario y solicitudes tipadas por IPC; sin servicio permanente adicional | Alta: I/O, IPC, respuestas perdidas y reap | Medio: aislamiento poison, nueva frontera de autorización/liveness | L: store más protocolo real | Media: retirar IPC en callers/despliegue |

## 3. Criterios de decisión

1. Preservar contratos y evidencia U1/U2 aceptados pesa más que reducir archivos.
2. Toda autoridad requiere adquisición propia viva y cadena S1; ningún DTO puede fabricarla.
3. Poison, commit y cleanup tienen estados separados y reproducibles con cortes reales.
4. El store no ejecuta acciones de lifecycle; los efectos requieren contratos adicionales liberados.
5. La evidencia parcial de un leaf no acredita producción, reinicio o persistencia ext4.

## 4. Recomendación · opción elegida y por qué

**Recomendada: organización O2.** Separa la custodia del kernel de la semántica CAS sin cambiar el alcance readonly. Evita la nueva frontera IPC de O3. O1 conserva menos fronteras internas, pero obliga a revisar el módulo U2 entero después de añadir I/O writable.

**Elegida: O2 por ROOT el 2026-10-11T14:39:03.061125+00:00**, bajo delegación vigente del propietario. Preserva U1/U2 y separa custodia de semántica CAS/ACK. O1 se descarta por concentrar cambios sobre observación aceptada. O3 se descarta por añadir IPC y liveness sin necesidad actual. La [propuesta ADR-0081](../../decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md) registra la decisión; ROOT adoptará sus destinos canónicos después de revisión/QA.

### 4.1 Tipos y autoridad que puede cruzar una interfaz

| Tipo cerrado propuesto | Contenido y autoridad |
|---|---|
| `FileIdentity` | `volume_serial:uint64`, `file_id:bytes16`, `canonical_path`, `kind:{directory,file}`; copia, sin HANDLE |
| `RootContext` | Ancla Windows/deployer ratificada, SID efectivo, volumen local NTFS y política S1; no se construye desde JSON o variables de entorno |
| `DeployerAuthority` | Emisión privada en runtime por entrada deployer confiable ratificada; owner registrado, política activa y autorización de operación; no se deserializa |
| `ChainLease` | Adquisiciones propias de root→proyecto→data→_storage, en orden; referencias a owners y lock hasta cierre/reap |
| `CreatedJournal` | Adquisición `FILE_CREATE/FILE_CREATED`, descriptor de creación y identidad observada; todavía sin ACK |
| `ReadLease` | Adquisición readonly propia, modo y geometría acreditados, cadena viva; sólo lectura/cierre |
| `WriterLease` | Adquisición RW propia, share cero, modo acreditado y cadena viva; exclusiva para store |
| `WriterGeometry` | Resultado G2 repetido en esta adquisición, B, modo, identidad y EOF; constructor privado después de consultas completas |
| `AlignedArena` | Base reservada, tamaño, dirección alineada, longitud y owner; su dirección nunca sale como capacidad pública |
| `JournalToken` | Versión store, identidad journal, journal_id, cadena ordenada, identidad proyecto, B, capacidad, generation, slot y digest COMMIT |
| `StoreSnapshot` | Copia exacta `JournalSnapshot` U1, token y estado diagnóstico; sin writer ni permiso de efecto |
| `StoreRequest` | ID ULID, bytes exactos U1 y hash derivado; acepta sólo `reserve`/`record` hoy |
| `CommitOutcome` | `commit_state:{sealed,rejected,unknown}`, `cleanup_state:{retained,closed,unknown}`, token opcional, causas primaria/secundarias y evidencia de barreras |
| `CloseOutcome` | `closed/unknown`; sin HANDLE reutilizable, estable en llamadas repetidas |
| `GatedNativeProbe` | Owner de archivo nuevo propio de prueba, scope exacto liberado por ROOT; sin ancla S1 acreditada ni capacidad de producto |
| `ProbeEvidence` | Copias de identidad/modo/geometría/conteos/barreras/bytes y grado `partial_native`; sin token/ChainLease/ACK |

Los enums son nominales, cerrados y ajenos al wire U1. Se rechazan bool, subclasses/dicts usados como capacidades, pseudo-handles y adquisiciones revocadas. Los constructores de leases/geometry/ACK no son públicos. Un scalar válido es insuficiente: owner, registro, modo y acquisition nonce deben coincidir bajo lock.

El token es una expectativa CAS portable entre sesiones del mismo store. No es secreto, autentificador, lease ni prueba de ACL actual. La API compara todos sus campos y los bytes exactos del request. Su hash no sustituye comparación de identidades ni cadena. Un token inicial interno usa generation=0, slot=None y digest cero después del bootstrap físico; no lo expone `open_existing` de un journal vacío.

No existe `JournalToken.from_dict` que abra un camino a autoridad. Importar una expectativa serializada sólo permite comparar sus campos bajo un writer ya acreditado. Un token fabricado que coincida en bytes no puede crear owner, cadena, S1 o permiso de efecto. Esta separación pertenece al modelo confiable de proceso; no promete resistir código malicioso en el mismo proceso autorizado.

### 4.2 API cerrada e integración

| Interfaz propuesta | Precondición y resultado |
|---|---|
| `admit_root(deployer_authority, project_components)` | Exige autoridad nominal viva emitida por deployer; adquiere ancla/padres reales, SID efectivo y S1; sólo devuelve RootContext tras acreditación |
| `create_new(root_context, operation_id, size_bytes, request_id)` | S1 acreditada y ausencia del final, seed y journal; crea sólo infraestructura nueva y sella generación inicial `reserved` |
| `open_read(root_context)` | `FILE_OPEN` del journal exacto; devuelve `ReadLease` y snapshot limpio, o diagnóstico bloqueante |
| `open_writer(root_context)` | `FILE_OPEN` RW exclusivo; reconsulta toda la cadena; no modifica bytes durante adquisición |
| `writer.read_snapshot()` | Lee capacidad completa por adquisición retenida; devuelve copia y token actual sólo si clean/head válido |
| `writer.commit(expected_token, request, snapshot)` | Revalida, decide U1, prueba igualdad request/snapshot y sella o replay; no ejecuta callback externo |
| `writer.recover_ack(request)` | Cadena clean y request exacto ya sellado; flush nuevo y relectura/revalidación; mismo token histórico, cero slots nuevos |
| `lease.close()` | Revoca autoridad local antes de llamada nativa; devuelve cierre separado e idempotente |
| `bootstrap_published(...)` | API futura distinta; necesita release de bootstrap y capacidades legacy acreditadas; no está liberada por `create_new` |

`project_components` es una tupla de nombres validados, sin paths arbitrarios ni handles. `DeployerAuthority` deriva de entrada deployer revisada y política activa fuera del journal, con identidad efectiva observada; no de un recibo JSON autocontenido. Reabrir reinicia esta adquisición. `RootContext` y leases se validan por tipo exacto, registro privado, owner y nonce bajo lock; no aceptan protocolo duck-typed.

`commit` recibe bytes U1 completos, pero el controller construye `snapshot` desde evidencias nominales y una transición liberada. El store garantiza CAS/bytes, no que un diccionario observado represente un montaje real. Es imposible obtener autorización de publish/attach/validate/detach llamando `record` directamente desde el CLI.

U1 sólo libera requests `reserve` y `record`. Sus enums de `intent` no liberan las acciones correspondientes. IDs de intent, completion y reconciliación deben ser solicitudes distintas; repetir el ID ya sellado devuelve replay del mismo commit. Antes del wiring lifecycle se concretará su correlación causal dentro de campos U1 existentes, sin inventar nuevas claves.

El controller extraerá los bytes históricos exactos `published_receipt_payload_b64`, validará `StorageReceipt` y llamará `PublishedDiskBinding.open(project_root, receipt)`. Ese binding aporta consulta del disco; no se transforma en capacidad de creación, rename o escritura. `ReceiptLease` se reserva al bootstrap legacy ratificado y permanece readonly.

### 4.3 Raíz, padres, seguridad y creación

El deployer aporta el contexto Windows confiable y el principal ratificado. La adquisición inicial abre el root real local, consulta identidad/volumen/tipo y acredita su correspondencia con ese contexto. No infiere ancla desde la letra de unidad, el journal o un ID en JSON.

El proveedor de ancla recibe la ubicación declarada del proyecto como configuración no autoritativa. Resuelve su root local, obtiene su volume GUID mediante Windows y abre ese root como directorio propio retenido. Compara volumen/ID, path normalizado DOS y GUID consultados desde ese handle. No acepta UNC, SUBST, mount-folder/reparse, root alternativo o respuesta ambigua en este perfil cerrado.

Para determinar el papel especial del root del sistema consulta `GetSystemWindowsDirectoryW`, resuelve su root y volume GUID y adquiere también su root real. Exige que la identidad y volumen del root candidato coincidan antes de aplicar la excepción owner TrustedInstaller. Resolver nombre GUID sólo localiza candidato; la metadata/S1 actuales de los handles acreditan pertenencia. Todos los accesos iniciales son readonly y no activan privilegios. [Microsoft: directorio Windows compartido](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getsystemwindowsdirectoryw), [volume GUID desde mount point](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumenameforvolumemountpointw), [path desde handle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew).

Estas consultas usan buffers acotados a 32.768 WCHAR, resultado no truncado, terminación y UTF-16 validados. Failure o cambios entre consultas bloquean. El GUID no se publica ni se usa como UUID ext4. El factory de RootContext sólo emite tras S1 del ancla y todos los padres seleccionados; owner/DACL aislados nunca bastan. La provisión ratificada del deployer y código confiable sigue siendo precondición externa, no algo que pruebe este factory por introspección.

Cada siguiente nombre pasa `_validate_component`: un componente exacto, sin separadores, ADS, nombres de dispositivo o alias. `NtCreateFile` usa `RootDirectory` del padre retenido. La arena conserva UTF-16, UNICODE_STRING, OBJECT_ATTRIBUTES, descriptor, IOSB y salida desde antes de entrar hasta completion. Nunca importa flags kernel-only a user-mode. [Microsoft: NtCreateFile user-mode](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile).

| Adquisición | Access específico | Share y opciones |
|---|---|---|
| Padre existente | TRAVERSE, READ_ATTRIBUTES, READ_CONTROL, SYNCHRONIZE | SHARE_READ|SHARE_WRITE, nunca SHARE_DELETE; DIRECTORY, SYNCHRONOUS_NONALERT y no-follow acreditado |
| Padre creador `_storage` | Lo anterior más ADD_FILE; ADD_SUBDIRECTORY sólo si crea dominio nuevo autorizado | Mismos shares; crear hijos no autoriza cambiar ACL o borrar siblings |
| Journal read view | READ_DATA, READ_ATTRIBUTES, READ_CONTROL, SYNCHRONIZE | Sólo SHARE_READ; NON_DIRECTORY, SYNCHRONOUS_NONALERT, NO_INTERMEDIATE_BUFFERING, OPEN_REPARSE_POINT |
| Journal writer | READ_DATA, WRITE_DATA, READ_ATTRIBUTES, READ_CONTROL, SYNCHRONIZE | Share=0; read options más WRITE_THROUGH; sin APPEND_DATA, DELETE, WRITE_DAC, WRITE_OWNER o DELETE_ON_CLOSE |

Sharing protege acceso de datos y DELETE según Windows. No promete excluir todo handle de metadata ni inmovilizar ACL contra un trustee confiable. Se revalida S1 antes/después de barreras. Un rival abierto antes también debe hacer fallar la adquisición incompatible. [Microsoft: sharing NtCreateFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile).

Todos los padres pasan S1 sobre OWNER/GROUP/DACL por handle. Se conserva la excepción TrustedInstaller exclusivamente en owner del root real del volumen del sistema. Grants outsider peligrosos, impersonación no ratificada, consultas incompletas y ACE no soportadas devuelven `SECURITY_UNACCREDITED` antes de crear objetos.

Crear dominio/journal utiliza `FILE_CREATE`, Information=FILE_CREATED, STATUS_SUCCESS y IOSB.Status=SUCCESS acreditados. Abrir utiliza `FILE_OPEN` y FILE_OPENED. No existe OPEN_IF, overwrite, supersede o adopción de archivo vacío. El dominio existente sólo se usa si su rol, identidad y S1 están acreditados; no se atribuye origen propio retrospectivamente.

El descriptor de objeto nuevo contiene owner=SID efectivo ratificado, GROUP explícito acreditado y DACL presente/protegida. Sólo incluye ALLOW explícitos para principal, SYSTEM y Administrators; las máscaras conocidas permiten operar a esos trustees. No hay herencia abierta, CREATOR_OWNER, SID personal embebido o cambios posteriores de ACL. La arena retiene los buffers SID/ACL referenciados por el descriptor durante creación. [Microsoft: SECURITY_DESCRIPTOR](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-security_descriptor), [owner referencia SID](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-setsecuritydescriptorowner).

Un directorio nuevo usa opciones DIRECTORY compatibles; no copia NO_INTERMEDIATE_BUFFERING del archivo. No-follow requiere testigo NT real por componente: metadata de reparse siempre rechaza y ninguna travesía de su destino puede acreditarse como éxito.

Antes de `create_new` se consultan los nombres final `studio-data.vhdx`, journal y seed bajo padres retenidos. Cualquier final existente causa CONFLICT, incluido SMOKE. FILE_CREATE del journal resuelve la carrera de su nombre; la ausencia previa del final no garantiza el NOREPLACE futuro. Cualquier aparición rival posterior se conserva y bloquea la publicación.

### 4.4 Modo, geometría, arenas e I/O exacto

El kernel privado no pasa `WriterLease` a `read_handle_geometry` ni fabrica un `_ObservedHandle`. Ejecuta las mismas consultas G2 sobre su adquisición propia y copia `MetadataObservation`/`GeometryObservation` para `derive_geometry_candidate`. Estas copias siguen sin autoridad. Sólo el owner privado verifica su origen, identidad y completion y construye `WriterGeometry`.

Se reconsultan FileFsSectorSizeInformation=11/28 bytes y FileAlignmentInformation=17/4 bytes, con IOSB exacto. Se conserva el rechazo G2 de unknowns, flags, offsets no acreditados y B fuera de 512..65536. FileModeInformation=16 produce un ULONG de 4 bytes; confirma NONALERT, NO_INTERMEDIATE_BUFFERING y WRITE_THROUGH del writer. ALERT, DELETE_ON_CLOSE, modo incompleto o bits no liberados bloquean. Mode es un subconjunto de CreateOptions; no demuestra share, owner o NON_DIRECTORY. [Microsoft: FILE_MODE_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_mode_information), [clases NT](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ne-wdm-_file_information_class).

La metadata antes/después exige mismo volumen/ID/path/cadena, archivo regular, un link, no delete-pending, reparse=0 y ausencia de sparse/compressed/encrypted/offline/device. Consulta volumen por handle confirma NTFS, persistencia ACL y no readonly. StreamInformation=22 se consulta con límite cerrado de 1 MiB; sólo stream de datos sin nombre. Buffer overflow, stream adicional o interpretación incierta bloquean, nunca equivalen a ausencia de ADS. [Microsoft: volumen por handle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumeinformationbyhandlew).

El parser StreamInformation valida alineación de 8 bytes, offsets de entradas sin ciclos/overlap, longitudes UTF-16 pares y rangos dentro de IOSB.Information. En NTFS exige una sola entrada, NextEntryOffset=0, nombre `::$DATA`, StreamSize=EOF y StreamAllocationSize=allocation. Retorno no soportado o Unicode inválido bloquea. [Microsoft: FILE_STREAM_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_stream_information).

La ABI nueva conserva el patrón x64 probado por U2: HANDLE/PVOID=8, NTSTATUS/LONG/BOOL=4, ULONG=4, ULONG_PTR=8, LARGE_INTEGER=8 e IOSB=16. Unicode/OBJECT_ATTRIBUTES conservan sus tamaños y offsets U2. Cada binding fija argtypes/restype antes de adquisición; símbolos ausentes o tamaños distintos rechazan. Las funciones NT proceden de ntdll; Win32 usa DLL con `use_last_error=True`.

| Binding nuevo | Firma y tamaños que fija el kernel privado |
|---|---|
| NtReadFile / NtWriteFile | NTSTATUS(HANDLE,HANDLE,PVOID,PVOID,IOSB*,PVOID,ULONG,LARGE_INTEGER*,ULONG*); últimos opcionales NULL salvo offset explícito |
| NtQueryInformationFile mode | NTSTATUS(HANDLE,IOSB*,PVOID,ULONG,ULONG); clase16, buffer4, Information4 |
| NtQueryInformationFile streams | Misma firma; clase22, arena alineada8, longitud e Information acotadas a 1 MiB |
| NtCreateFile | Firma U2 de once argumentos; AllocationSize LARGE_INTEGER* opcional, descriptor en OBJECT_ATTRIBUTES retenido, sin EA |
| FlushFileBuffers / CloseHandle | BOOL(HANDLE); BOOL no-cero requerido; captura GetLastError inmediatamente al FALSE |
| VirtualAlloc | PVOID(PVOID,SIZE_T,ULONG,ULONG); devuelve base propia no-NULL |
| VirtualFree | BOOL(PVOID,SIZE_T,ULONG); base original, size0 y MEM_RELEASE |

Los buffers de query usan sentinels y sólo se copian después del retorno completo, bajo lock. Information menor/mayor que la estructura fija rechaza. No se transfiere un pointer de la arena al snapshot, token o diagnóstico.

`AlignedArena` reserva con VirtualAlloc MEM_RESERVE|MEM_COMMIT y PAGE_READWRITE. Para longitud n reserva n+B-1 con overflow comprobado; alinea la dirección hacia arriba a B y comprueba que el intervalo cabe. No presupone que page alignment cubra sectores de 64 KiB. Retiene base original y libera sólo esa base con VirtualFree(base,0,MEM_RELEASE). [Microsoft: File buffering](https://learn.microsoft.com/en-us/windows/win32/fileio/file-buffering), [VirtualAlloc](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc), [VirtualFree](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualfree).

Cada I/O utiliza `NtReadFile`/`NtWriteFile` con adquisición retenida, Event/APC/Key NULL, offset LARGE_INTEGER explícito no negativo y ULONG length. Offset, longitud y dirección son múltiplos de B. No hay seek compartido, append, escritura por path ni mmap. STATUS_SUCCESS, IOSB.Status=SUCCESS e Information=longitud exacta son obligatorios. Short read dentro del EOF reservado o short write bloquean; no se completa un parcial con retry. [Microsoft: NtReadFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntreadfile), [NtWriteFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntwritefile).

La receta usa WRITE_DATA explícito y excluye APPEND_DATA incompatible según NtCreateFile. Microsoft documenta GENERIC_WRITE para FlushFileBuffers, cuyo mapeo incluye APPEND_DATA. Por ello esta receta exige testigo nativo de FlushFileBuffers exitoso sobre exactamente este handle/access/mode antes de admitir ACK. No afirma que las páginas citadas prueben por sí solas esa combinación mínima. Si falla, gate cerrado y concreción de acceso adicional; ningún fallback amplía derechos o desactiva buffering. [Microsoft: FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers).

### 4.5 Inicialización física y conservación de EOF

Se consulta G2 en el journal recién creado, todavía vacío. B fija `JournalLayout`: payload=ceil(1MiB/B)*B; slot=payload+2B; capacidad=B+64*slot. Para B=4096 la capacidad es 67.637.248 bytes. No se elige B desde fixture, root distinto o una read view anterior.

El writer inicial escribe ceros reales sobre toda la capacidad con chunks alineados de hasta 1 MiB; después escribe la cabecera exacta U1 en el primer bloque. No usa truncate, SetFileValidData, sparse o allocation como prueba de inicialización. AllocationSize inicial puede reservar espacio, pero nunca sustituye estas escrituras.

Después comprueba EOF exacto y allocation>=capacidad, flush del mismo handle y relectura completa igual a cabecera más ceros. La inspección U1 debe ser clean sin head. Este estado físico no da autorización de efecto ni ACK de reserva. Sólo el commit inicial sellado y revalidado genera el token generation=1.

La cabecera, EOF y todos los slots usados quedan inmutables tras bootstrap. Una operación regular verifica EOF==capacidad y B actual==B cabecera. No extiende, rellena huecos, corrige bytes o recicla slots. Un error durante inicialización preserva el archivo incompleto, revoca creación y bloquea; un nuevo `create_new` no lo sobrescribe.

### 4.6 CAS, PREPARE, COMMIT y ACK

La lease tiene un RLock para toda operación del store; una adquisición/arena tiene un owner único. `commit` no llama herramientas, runners, callbacks o código externo bajo ese lock. El controller puede conservar la exclusión del journal entre intent y completion, pero ejecuta el efecto fuera del lock y bajo su contrato propio.

| Paso | Comprobación obligatoria |
|---|---|
| Adquirir writer | Toda cadena S1, modo/G2/EOF y metadata actuales; releer capacidad completa por este handle |
| Preflight CAS | Inspección clean/head; identidad nativa contra envelope; comparar token completo; validar request exacto y snapshot U1, índice siguiente y previous digest |
| Replay | Buscar request exacto en toda cadena; no requiere token esperado actual si la identidad/cadena del token corresponden; bytes distintos=REQUEST_CONFLICT |
| Append | `decide_request` debe devolver append; slot totalmente cero y siguiente contiguo; cabecera y generaciones anteriores preservadas |
| PREPARE | Escribir frame completo U1 de B+payload_bytes; exact count; FlushFileBuffers; revalidar y releer ese rango idéntico |
| COMMIT | Escribir bloque B separado U1; exact count; FlushFileBuffers; revalidar cadena/ACL/G2/EOF y releer journal completo |
| Seal | Inspección clean, head exacto recién generado, request/predecesor/digest/snapshot iguales; entonces commit_state=sealed |
| ACK | Entregar token sólo después de Seal, ambas barreras exitosas y owner no poisoned; close no sustituye una barrera |

Antes de PREPARE, snapshot debe conservar project/journal/parent identities de esta adquisición, operación, cabecera y head. `record` no puede alterar historia v1 previa, bytes históricos published o tamaño. Los controles U1 se ejecutan también contra el journal posterior; un hash aislado o un head suministrado por caller no basta.

Replay hace flush nuevo, revalidación y lectura completa antes del ACK recuperado. Puede devolver un token de generación histórica si existen commits posteriores; no rebobina el head. El snapshot de resultado y el head actual se distinguen en la respuesta. Un intent replayed no autoriza ejecutar de nuevo el efecto.

El ACK de una intención permite al controller iniciar sólo su efecto exacto después de revalidar sus capacidades. El ACK de completion permite devolver resultado exitoso. Un ACK del store no acredita que un comando externo ocurrió. El controller deberá comprobar transición/resultados, admisión y correlación antes de solicitar cada commit.

### 4.7 Custodia, poison y cierre

Antes de cada llamada nativa se registran arena, adquisición, argumentos, buffers y owner. La custodia abarca retorno, reconocimiento y registro de la adquisición, incluyendo éxito seguido de excepción Python. El owner mantiene referências fuertes a toda cadena y buffers hasta completion acreditada o retirada real del proceso.

STATUS_PENDING, excepción durante la llamada, completion inconsistente o interrupción antes de registrar resultado revocan toda autoridad del contexto. No se espera con timeout para declarar que el kernel acabó. No se libera arena, se cierra scalar ni se reintenta I/O incierto. Un registro global retiene los recursos; un supervisor confiable termina y reap al proceso propietario antes de otro recovery.

Un error nativo completado puede liberar su arena sólo después de acreditar completion y registrar el fallo. Desde la primera llamada de escritura, cualquier fallo devuelve COMMIT_UNKNOWN salvo evidencia suficiente de sealed obtenida después. Una falla read/query anterior a escritura rechaza y revoca lease; no modifica historial para dejar un diagnóstico.

Close reserva primero CloseOutcome=unknown, retira el scalar de autoridad y llama CloseHandle una vez. FALSE, excepción o interrupción preservan causas y owner; llamadas posteriores devuelven el mismo outcome sin repetir el scalar. Si existe I/O incierto, no llama CloseHandle hasta retirada del proceso. Las arenas completas se liberan tras completion; failure de VirtualFree se conserva separado. [Microsoft: CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle).

`sealed/unknown` conserva que el commit quedó sellado y que cleanup no se acreditó. CLI devuelve error con esa distinción; nunca oculta el commit ni repite efecto. Si una interrupción acontece al exponer ACK, la respuesta se considera perdida y recovery verifica el request. El diagnóstico no contiene HANDLE, dirección de buffer o capacidad reutilizable.

### 4.8 Cutpoints C0–C7 y recovery completo del store

| Corte | Estado conservador y siguiente acción |
|---|---|
| C0: antes PREPARE | Rejected, cero escritura; token esperado no consume slot |
| C1: dentro PREPARE/body | Unknown; preservar, reacreditar y clasificar todos los bytes; nunca completar parcial por inferencia |
| C2: tras write antes flush1 | Unknown; misma clasificación, sin COMMIT ni efectos |
| C3: flush1/relectura completas | PREPARE sin COMMIT no es head; slot conservado y gate cerrado |
| C4: dentro COMMIT | Unknown; COMMIT parcial no autoriza prefijo operativo |
| C5: COMMIT escrito antes flush2 | Unknown; reopen clean puede recuperar mismo request con barrera nueva; bytes inválidos bloquean |
| C6: flush2/relectura antes ACK | Reacreditar cadena completa, flush nuevo y replay del mismo token; cero nuevo slot o efecto |
| C7: cleanup/close | Separar commit sealed de cleanup unknown; retirar/reap owner si incierto antes de recovery |

`open_existing` observa todas las generaciones, no sólo la última. Journal ausente, ID distinto, EOF incorrecto, header dañado, hueco, fork, COMMIT inválido o cambio de historia producen rechazo con conservación. No se reconstruye desde seed, mtime o SHA del disco.

U1 devuelve `incomplete_tail` sin head operativo y `decide_request` devuelve JOURNAL_BLOCKED. Su generación es slot_index+1 y no acepta sucesor después del hueco. Este store respeta ese rechazo para C1–C4 y para C5 inválido. La clasificación y preservación son comportamientos parciales del store; no completan recovery del producto. La reanudación de una cola bloqueada continúa como trabajo exigido y pendiente.

La intención previamente sellada puede existir antes de un fallo externo o de completion. Si la cadena sigue clean, el controller futuro podrá reconciliar realidad y sellar una completion con request distinto. Si la cola del journal es incomplete/corrupt, ni la realidad del efecto permite escribir un sucesor bajo U1.

La resolución causal independiente de esa cola exige otra concreción: autoridad fuera del archivo dudoso, autenticidad/procedencia de última intención, prueba de efecto/ausencia, retención de bytes/IDs y protocolo de vinculación hacia un journal nuevo sin sobrescribir ninguno. Debe definir replay de árbol viejo, atomicidad/ACK de esa vinculación, exclusión y crash entre archivos. U1 actual permanece intacto; no se habilita migración, compacto, skip, overwrite o adopción con este diseño.

El producto final conserva la exigencia de recovery persistente: además del store necesita publicar/attach/validate/detach y la resolución anterior si pretende reanudar tras esas colas. No se sustituye esa verificación por éxito de tests que sólo acreditan rechazo.

### 4.9 Invariantes J01–J10 y tests causales futuros

Todos los casos siguientes son requisitos para RED futuro. No se ejecutaron tests o escrituras durante esta pasada. Fault injection prueba causalidad; sólo los casos marcados NT real prueban semántica Windows.

| ID | Contrato verificable | RED y testigo exigido |
|---|---|---|
| J01 | Writer excluye READ/WRITE/DELETE del journal | NT real: rival anterior/posterior, read view, rename/delete/write; sentinels intactos y procesos propios reap |
| J02 | Read view retiene READ y sólo SHARE_READ | NT real: dos readers compatibles, writer bloqueado mientras reader vive; writer adquiere tras cierre acreditado |
| J03 | Head readonly no autoriza CAS | NT real: dos procesos con mismo token; sólo uno append, otro stale/busy; cambio de padres/token rechaza sin escritura |
| J04 | Header/EOF/slots usados inmutables | Bytes before/after exactos en NT real; short write, header mismatch, EOF distinto y full rechazan sin repair |
| J05 | Intención y completion necesitan sus ACK | Fault causal: flush1/flush2 fallan, callback no empieza sin intent ACK; doubles no acreditan efecto real |
| J06 | Sólo I/O por handles retenidos y cadena actual | NT real: objetos rivales/alias, rename durante custodia, ACL outsider nueva propia; cero reopen por nombre observado |
| J07 | Conteos exactos y bloques disjuntos | RED short counts/offset/length/address/mode; NT real Write→Flush→Read exacto, B acreditado del mismo handle |
| J08 | Sólo cadena íntegra autentica estructura | Corrupción por bytes controlados en archivos propios, forks/COMMIT parcial; no head viejo operativo ni ACK |
| J09 | Incertidumbre retira autoridad antes del fallo | RED PENDING/interrupción/éxito antes registro/Close FALSE/VirtualFree fallo; arenas retenidas, scalar no retried |
| J10 | Replay exacto de toda cadena | NT real C6/C7, request viejo sellado con head posterior, conflicto de bytes; mismo token y cero nuevo slot/efecto |

El harness de crash es un subprocess propio y archivos nuevos privados liberados expresamente por ROOT. El padre espera un checkpoint externo verificable, termina al hijo realmente, reap y reabre con nuevas adquisiciones. Conserva stdout/stderr, PID real, bytes, file IDs, mode, geometry, hashes y errores originales. No simula kill con una excepción.

Para C1/C4 los checkpoints deben poder cortar una transferencia dividida exclusivamente por harness privado o acreditar un parcial real; un mock short-write no cuenta como torn-write nativo. No se declara que un kill siempre interrumpe un sector atómicamente. Se clasifican los bytes reales tras cada corte.

Testigos de ACL, reparse, streams y adversarios modifican únicamente objetos nuevos propios. La cadena real del host conserva su rechazo S1. El kernel puede demostrar creación/I/O/leaf en fixture parcial, pero ese resultado nunca construye ChainLease confiable ni ACK de producción. Un caso positivo full-chain requiere provisión ratificada y observada, no mock trusted root.

`GatedNativeProbe` es la única interfaz de testigo parcial: su factory exige un scope ROOT que nombra el namespace nuevo propio, padres retenidos y ausencia de nombre antes de FILE_CREATE. Retiene descriptor cerrado, acquisition owner y arenas; aplica las mismas reglas mode/G2/I/O/poison/cierre del kernel. Puede escribir/leer/flush frames de prueba sólo sobre ese archivo nuevo. Devuelve `ProbeEvidence` y nunca llama el factory de RootContext/ChainLease ni `JournalStore.commit` con un bypass de trust.

No existe promoción probe→writer de producto, `trusted=True`, desactivación S1 o ACK parcial. Los tests puros/dobles de CAS verifican la máquina del store; el testigo native prueba kernel real. Sólo un test de store sobre cadena provisionada S1 prueba ambas juntas. La cobertura o ejecución de esas categorías separadas no fabrica ese positivo integrado.

El bootstrap físico se prueba además en creación/cero/cabecera/flush/generación inicial. Tras cada corte se exige conflicto posterior y conservación de archivo incompleto. Es una categoría distinta de C0–C7; esta definición única evita duplicar su requisito en el contrato.

La cobertura whole de módulos nuevos/cambiados debe alcanzar 80% sin exclusiones, con revisión fresca A/B/C y QA independiente. Ext4 real, admisión, mount, namespaces, recovery y backup/restauración siguen pruebas separadas de aceptación T05/M1.

## 5. Impacto en módulos y ficheros

Las rutas existentes se comprobaron en el checkout. Los archivos nuevos son propuestas explícitas; no existen por esta pasada.

| Ruta | Impacto de organización recomendada | Tipo |
|---|---|---|
| `scripts/storage_journal.py` | Reusar codec/wire U1 sin cambios; conservar bloqueo de colas | Existente, preservado |
| `scripts/storage_journal_windows.py` | Reusar tipos/copias, principal y evaluación S1/G2 puros; no ampliar ObservedHandle | Existente, preservado |
| `scripts/storage_journal_windows_io.py` | Kernel privado de adquisición propia, arenas, mode/geometry/metadata y I/O | Nuevo propuesto |
| `scripts/storage_journal_store.py` | ChainLease, create/open, tokens, CAS, replay, ACK y diagnóstico recovery | Nuevo propuesto |
| `tests/test_storage_journal_windows_io.py` | ABI/ownership/I/O/short counts/poison/cierre y testigos NT | Nuevo propuesto |
| `tests/test_storage_journal_store.py` | S1/CAS/ACK/replay/cutpoints y bootstrap físico reales | Nuevo propuesto |
| `scripts/storage_receipt_store.py`, `scripts/storage_operator.py` | Consumir leases readonly existentes para bootstrap/binding futuros | Existentes, preservados |
| `packages/storage-guard/studio_storage_guard/receipt.py` | Payload v1 intacto, no fases nuevas | Existente, preservado |
| `scripts/storage_lifecycle.py` | Futuro controller de transiciones/evidencias/admisión; necesita otra concreción | Nuevo propuesto no liberado |
| `scripts/storage_offline.py`, `scripts/storage_publish.py`, `scripts/storage_attach.py` | Futuro wiring único al controller; retirar writers JSON por ruta | Existentes, fuera de escritura actual |
| `packages/storage-guard/studio_storage_guard/provision.py` | Auditoría readonly futura de dominio existente, distinta de new-empty | Existente, concreción pendiente |

La infraestructura fija `data/_storage/storage-control.journal` y `data/_storage/studio-data.vhdx`. Seed v1, raw e incoming necesitan nombres/capacidades de lifecycle acreditados. No se agregan identidades ajenas al parent_chain cerrado U1. La propuesta no toca ninguno de estos datos.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Ancestros actuales permiten MODIFY outsider | Acreditado en contexto ROOT, nueva adquisición debe confirmarlo | Impide full-chain y producción | S1 rechaza sin crear; conservar evidencia parcial separada |
| Generic-write de documentación flush frente a no-append NT | Incertidumbre de documentación | Puede impedir ACK con receta mínima | Testigo exacto access/mode/FlushFileBuffers; si falla, concreción nueva sin fallback |
| Cola incompleta no tiene avance causal U1 | Certeza del codec vigente | Impide reanudación automática después de ciertos crashes | Clasificación/preservación; contrato independiente antes de habilitar recuperación adicional |
| Native call pendiente o interrupción Python | Posible | Arenas/handles aún usados por kernel | Revocación y custodia hasta retirada/reap real del owner |
| Namespace bootstrap perdido tras host crash | Posible, no probado | Journal/final no correlacionables | Unknown y conservación; ensayos de host separados, jamás adopción desde hash |
| Hardware no honra write-through/flush | Desconocida | Pérdida de datos tras powerloss | ACK condicionado a barreras observadas; no garantía absoluta ni evidencia subprocess como sustituto |
| Metadatos/ACL cambian por trustee confiable | Posible dentro de frontera | Invalida capacidad actual | Revalidación por handle en cada barrera; admitir sólo controller/deployer ratificados |
| Codec reserve/record interpretado como autorización lifecycle | Evitable | Efectos sin intención o evidencia real | API controller nominal, release explícita por acción y negativa CLI sin journal |

No se llama fsync a FlushFileBuffers ni se usa flush de directorio o volumen como sustituto. No hay atomicidad conjunta entre journal, rename y montaje. [Microsoft: File caching](https://learn.microsoft.com/en-us/windows/win32/fileio/file-caching).

## 7. Preguntas abiertas

- ROOT eligió O2. Revisión/QA del contrato y adopción siguen pendientes antes de liberar código o experimentos. La autoridad ya delegada permite a ROOT liberar después pruebas propias reversibles; no exige otro permiso humano para cada test.
- Producción requiere autorizar expresamente una nueva cadena dentro del proyecto que cumpla S1, con contexto/deployer y SID ratificados. Si sus ancestros siguen mutables por outsiders, la creación de un leaf protegido no basta. Una remediación de padres existentes necesita decisión y autorización separadas, evidencia de impacto y nueva revalidación; este diseño no la propone como atajo ni la ejecuta.
- ROOT liberará objetos nuevos propios para testigos NT parciales después de revisión/QA del contrato, dentro de la delegación ya vigente. Los distinguirá del positivo full-chain; esta selección no inicia experimentos.
- La combinación de access específico sin APPEND_DATA y FlushFileBuffers requiere el testigo nativo indicado. Su éxito funcional no reemplaza la revisión de esta frontera documental.
- El bootstrap legacy necesita contrato separado para snapshot/identidades ratificados, retención de ReceiptLease y PublishedDiskBinding, fase inicial y seed exacto. SMOKE no se adopta como producción.
- Publish, attach, validate, quiesce, detach y reconcile necesitan correlación request/intent/completion, evidencias nominales y admisión serializada. Conservan admin/ext4/UUID/probes reales; sus requests no se habilitan ampliando sólo el enum U1.
- La resolución causal independiente de una cola bloqueada requiere el protocolo descrito en §4.8 antes de afirmar recovery integral del producto. El wire U1 actual y sus rechazos permanecen vigentes.
- Powerloss/reinicio real y cadena S1 de producción siguen sin evidencia. No existe aceptación técnica T05/M1 por este documento.

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-11 | Segunda pasada privada: ROOT fija O2; ADR-0081 propuesta, tabla comparativa única y fronteras físicas pendientes |


## Acta de adopción ROOT — 2026-10-11T15:37:47.375671+00:00

Revisión2A/B0gaps yQA documental95/95,gateverde; ROOTverifica60payload/21fuentes/19guardascanónicas/2seams/7tools. ContratoO2incorporado, sin implementación ni evidencia nativeFlush/ACK/fullchainS1/bootstrap/lifecycle/causalrecovery/ext4/E2E/manuales. Esos gates siguen obligatorios. Implementación futura sólo por unidad liberada yTDD/revisión/QA; no cierreT05/M1. Originales privados íntegros.


## Concreción del kernel privado K1

La [concreción ABI y memoria K1](storage-journal-kernel-design.md) fija C2 y los contratos previos al RED. El contrato K1 está aceptado documentalmente; la implementación y aceptación de producto K1, T05 y M1 siguen pendientes. No sustituye el store O2, S1 full-chain, G2, ACK, bootstrap, lifecycle, recovery causal o ext4.
