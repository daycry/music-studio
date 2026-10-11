---
design: storage-journal-kernel-concretion
titulo: Contrato pre-RED de ABI y memoria del kernel privado M1 T05
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md
evaluacion: n/a
plan: docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md
adr: docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md
opcion_elegida: C2
recomendada: C2
validada_por: ROOT bajo delegación expresa del propietario
validada_fecha: 2026-10-11
validacion_via: elección explícita C2 recibida del orquestador
estado_propuesta: FIX1 documental; elección C2 registrada; pendiente revisión2 A/B, QA2 y adopción ROOT
revision_documental: FIX1 pendiente revisión2 A/B y QA2
quota_accounting: requested_bytes_including_padding
namespace_opciones: C1/C2 son seams internos; no son O2/S1/G2 ni gates históricos
decisiones_fijadas: ADR-0075/O2, ADR-0076/S1, ADR-0078/G2, ADR-0081/O2
canonical_adopted: true
implementation_released: false
actual_usage: null
generacion:
  fuente: estimado
  medidor: ROOT; sin marcador propio concurrente
  tokens_reales: null
  coste_real_eur: null
  horas_ia_reales: null
---

# Diseño — Qué implementa K1 y qué autoridad no puede emitir

> Propuesta privada con C2 elegida por ROOT bajo delegación expresa del propietario. Spec M1 aprobada y contrato O2/ADR-0081 incorporado tras revisión2 y QA95. ROOT confirma un nuevo gap Important de QA1: §4.4 confundía cuota solicitada y reserva OS. FIX1 aclara esa cuota; requiere revisión2 A/B, QA2 y adopción antes del RED. Review1 no constituye adopción de esta concreción. TDD n/a: prosa y arquitectura.

| Campo | Valor |
|---|---|
| Estado | FIX1 documental en borrador; elección C2 registrada; pendiente revisión2 A/B, QA2 y adopción; ninguna unidad aceptada o liberada |
| Opción elegida | C2 por ROOT bajo delegación expresa del propietario |
| Recomendación | C2: fachada de custodia y binding Windows separado, dentro del kernel privado O2 |
| Validación | Elección explícita C2 de ROOT registrada el 2026-10-11; implementación no liberada |
| Fuentes | 18 preimágenes fijadas por `release-root.receipt.json`: este diseño y 17 fuentes ajenas preservadas; referencias primarias Microsoft consultadas |
| Ownership actual | Sólo este diseño dentro de `snapshot/` y evidencia propia del namespace FIX1; otras 17 fuentes readonly, actores concurrentes |

Las rutas de fuentes se expresan respecto al repositorio. Para esta lectura se usó exclusivamente su copia bajo `snapshot/`, salvo documentación del kit. Las rutas nuevas son propuestas, no archivos implementados. Los enlaces externos apoyan hechos de ABI; las reglas más restrictivas son decisiones de este contrato.

## 1. Contexto y restricciones

`scripts/storage_journal.py` contiene el codec U1 aceptado. `scripts/storage_journal_windows.py` contiene observación readonly, política pura S1 y derivación G2. Sus SHA del release permanecen como preimágenes obligatorias. Ninguna de esas observaciones emite permisos de writer.

`storage-journal-store-design.md` y ADR-0081 fijan kernel privado y store separados. El kernel será propietario de sus adquisiciones y buffers. El store acreditará trust, CAS, PREPARE/COMMIT, replay y ACK. Esta propuesta concreta seams internos y la primera unidad; conserva el objetivo íntegro de T05.

La Constitución §2 mantiene datos dentro del proyecto y sólo al server como escritor de SQLite. K1 reserva memoria del proceso Windows propio. No abre archivos, consulta ACL, crea anclas, accede a SQLite o usa GPU. Tampoco importa U2 para reutilizar sus clases privadas o sus globals de custodia.

La evidencia experimental ya incorporada sólo demuestra acceso exacto `0x00120083`, share0, options `0x0020006a`, FileMode `0x2a`, B65536 y Write→Flush→Read exacto. Fueron tres archivos de 131072 bytes. No hubo APPEND_DATA ni ampliación de derechos.

Los tres exits originales1 por contador global134→135 se conservan. Cada proceso cerró diez handles propios y liberó una arena. El control UUID independiente tuvo deltas1/0/0. No identifica el handle interno ni prueba ausencia universal de fugas. K1 no reutiliza ese resultado como QA de producto, ACK, full-chain S1 o powerloss.

### Fuentes primarias consultadas el 2026-10-11

| Fuente Microsoft | Hecho utilizado y límite |
|---|---|
| [VirtualAlloc](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc) | Reserva/commit en el proceso llamador; SIZE_T; base o NULL. Con addressNULL redondea dwSize a páginas; commit no mide memoria física residente. K1 usa RESERVE|COMMIT y READWRITE. |
| [VirtualFree](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualfree) | MEM_RELEASE usa la base original y tamaño0; BOOL no-cero acredita éxito. No liberar dirección alineada interior. |
| [IO_STATUS_BLOCK](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_io_status_block) | Unión NTSTATUS/PVOID e Information ULONG_PTR. Retorno no-PENDING gobierna; exigir también IOSB coherente es política restrictiva propia. |
| [UNICODE_STRING](https://learn.microsoft.com/en-us/windows/win32/api/ntdef/ns-ntdef-_unicode_string) | USHORT, USHORT, PWSTR; Length/MaximumLength en bytes. La terminación no cuenta en Length. |
| [OBJECT_ATTRIBUTES](https://learn.microsoft.com/en-us/windows/win32/api/ntdef/ns-ntdef-_object_attributes) | RootDirectory retenido permite nombre relativo; descriptor y ObjectName son punteros. Su lifetime pertenece al caller. |
| [NtCreateFile user-mode](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile) | Once argumentos; handle de salida e IOSB; acceso/options específicos. El binding no equivale a autorización para llamar. |
| [NtReadFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntreadfile), [NtWriteFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntwritefile) | Nueve argumentos; ULONG length, LARGE_INTEGER* offset y buffer del caller. K1 sólo fija firmas. |
| [CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle) | BOOL y fallo; handles inválidos/pseudo pueden provocar excepción bajo debugger. K1 no acepta ni cierra handles. |
| [FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers) | BOOL y acceso documentado GENERIC_WRITE; la receta mínima tiene testigo funcional separado, no garantía absoluta. |
| [File buffering](https://learn.microsoft.com/en-us/windows/win32/fileio/file-buffering) | Buffer y transferencia requieren alineación acreditada; page alignment no reemplaza comprobar el intervalo propio respecto a B. |

Los tamaños/offsets x64 de §4.3 son comprobaciones propias apoyadas por el patrón ABI congelado. No se atribuyen a Microsoft límites de política, exclusión Python, absence-of-leaks o aceptación de producción.

## 2. Opciones (2)

Ambas conservan `scripts/storage_journal_windows_io.py` como única interfaz privada del kernel. El store permanece en `scripts/storage_journal_store.py`. No hay opción de ampliar U2, otorgar trust con JSON o sustituir S1 por un leaf protegido.

### C1 — Kernel en un archivo, binding construido bajo factory

ABI, DLLs, registro y memoria viven en `scripts/storage_journal_windows_io.py`. Las clases ctypes se construyen dentro de una factory tardía. El import del módulo puro sigue sin cargar ctypes o DLLs. Las pruebas CPU usan las operaciones privadas de memoria y las Windows inspeccionan el binder real.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: un archivo, clases ABI tardías y mayor mezcla de responsabilidades |
| Riesgo | Medio: una edición futura de adquisición puede introducir cargas Windows durante import o alterar memoria |
| Coste relativo | S: menos fronteras de import; mismos controles de autoridad y QA |
| Reversibilidad | Alta: separar posteriormente el binder conserva API opaca y wire U1 |

### C2 — Fachada de custodia y binding Windows separado

`scripts/storage_journal_windows_io.py` contiene registro, lock, límites, DTO y `AlignedArena`. `scripts/storage_journal_windows_abi.py` contiene sólo estructuras y binding nativo. La fachada importa el segundo archivo únicamente después del gate Windows x64. Las operaciones del backend cruzan un seam privado nominal de memoria, sin emitir capacidades de archivo.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: dos archivos nuevos y contrato de backend cerrado |
| Riesgo | Medio-bajo: carga Windows aislada; exige controlar identidad y procedencia de backend/owner |
| Coste relativo | M: verificar ambas fuentes completas y su integración |
| Reversibilidad | Alta: unir archivos preservando API; ningún cambio a U1/U2 ni historial |

## 3. Criterios de decisión

1. Mantener preimágenes U1/U2 aceptadas pesa más que reducir archivos.
2. Una capability debe depender de objeto exacto registrado, owner vivo y proceso actual. Un scalar, hash o DTO nunca la sustituye.
3. La incertidumbre conserva recursos antes de exponer el fallo. La liberación nunca depende de GC o de un timeout.
4. El import unsupported debe ser verificable sin cargar ctypes ni DLLs Windows. Los dobles CPU no acreditan ABI o kernel nativos.
5. K1 debe tener una frontera implementable y cerrada. La cadena full S1, store y lifecycle permanecen obligatorios después.
6. El split debe permitir medir cada archivo whole >=80%, sin omitir binding, cleanup, errores o ramas incómodas.

## 4. Recomendación · opción elegida y por qué

**Recomendación: C2.** Aísla la carga nativa y permite probar custodia en Linux sin importar ctypes. Preserva el kernel privado de O2 y evita modificar el observador U2.

**Elegida: C2 por ROOT bajo delegación expresa del propietario, registrada el 2026-10-11.** ROOT mantiene §4.1–4.9 y las cuatro rutas K1 propuestas. C2 aísla el binding Windows, mantiene import unsupported puro y preserva U1/U2, según los criterios1/4/6. C1 se descarta por mezclar binding y custodia en el mismo archivo. La elección no acredita revisión, QA, adopción o implementación.

### 4.1 Qué constituye K1

K1 implementa ABI cerrada, reserva de memoria alineada, copia de bytes, owner, registro, locks, revocación y liberación acreditada. Puede crear una capability de memoria propia. No implementa una adquisición de archivo ni un calling seam arbitrario de funciones nativas.

El binder puede fijar firmas de I/O futuras, pero la fachada no entrega las funciones ni un método `call(function, *args)`. K1 no implementa NtCreateFile, NtReadFile, NtWriteFile, FlushFileBuffers o CloseHandle como operaciones invocables del kernel. Un testigo K1 nativo sólo puede llamar VirtualAlloc/VirtualFree y copiar dentro de su memoria propia.

No existen `RootContext`, `WriterLease`, `ChainLease`, `WriterGeometry`, `GatedNativeProbe` o ACK construibles por K1. Sus tipos/factories se liberarán en las unidades respectivas. `AlignedArena` no acepta un address, HANDLE, ctypes pointer, dict o memoria ajena como entrada.

### 4.2 API exacta privada de K1 y DTO

Los nombres siguientes pertenecen a `scripts/storage_journal_windows_io.py`. No son una API HTTP, CLI o formato persistido. No se serializan capabilities ni se admiten constructores públicos.

| Firma propuesta | Precondición y resultado |
|---|---|
| `_new_memory_context() -> _MemoryContext` | Gate Windows x64, binder completo y validado; crea owner sólo de memoria, pid actual y backend nativo propio. No recibe path, handle, trusted flag o backend del caller. |
| `_allocate_aligned(context, *, length: int, alignment: int) -> AlignedArena` | Contexto exacto registrado y vivo; límites §4.4. Reserva propia y registro antes de retornar capability. |
| `_arena_info(context, arena) -> ArenaInfo` | Contexto/arena exactos, origen y estado registrados; devuelve copia readonly sin direcciones. También informa estado revoked/closed del objeto propio. |
| `_arena_copy_in(context, arena, *, offset: int, data: bytes) -> None` | Arena live, ambos owners coinciden, bytes exactos y rango válido; copia todos los bytes sin devolver vista. |
| `_arena_copy_out(context, arena, *, offset: int, length: int) -> bytes` | Arena live y rango válido; devuelve bytes nuevos independientes. No devuelve memoryview, ctypes array o puntero. |
| `_close_arena(context, arena) -> CloseOutcome` | Capability propia, incluidos estados revoked/closed; resultado estable. Reserva unknown y revoca antes de VirtualFree una sola vez. |
| `_close_memory_context(context) -> CloseOutcome` | Revoca todas sus arenas; cierra las liberables en orden inverso, cada una como máximo una vez; resultado agregado estable. |

`_MemoryContext` y `AlignedArena` son clases opacas distintas, con slots y factory interna. No tienen constructor útil fuera de la factory. No implementan `__int__`, `__index__`, buffer protocol, pickle o copia que conserve autoridad. `repr` no publica campos internos.

La validación usa `type(x) is ExpectedType`, referencia de objeto mediante `is` y pertenencia al registro. Nunca usa duck typing, igualdad sobrecargada, `id` persistido, hash suministrado o nonce público. Constructor eludido con `object.__new__`, subclass, copy y objeto deserializado rechazan al carecer de entrada auténtica.

| DTO frozen, campos exactos | Reglas |
|---|---|
| `ArenaInfo(length:int, alignment:int, state:str, provenance:str)` | state `live/revoked/closed/unknown`; provenance `native_windows_x64/cpu_double`; sin address/base/pid reutilizable. Son observaciones. |
| `CloseOutcome(state:str, causes:tuple[FailureDiagnostic,...])` | state `closed/unknown`; causes copiadas e inmutables; ningún scalar reusable. Primer unknown queda reservado antes de llamada. |
| `FailureDiagnostic(code:str, operation:str, win32_error:int-or-None, ntstatus:int-or-None)` | Enums cerrados §4.7; códigos numéricos 0..2^32-1, sin mensajes nativos o interpolación del caller. |
| `_AllocResult(base:int-or-None, win32_error:int-or-None)` | DTO interno exacto; nunca sale del backend/registro. NULL completado distingue fallo conocido de retorno incierto. |
| `_BoolResult(success:bool, win32_error:int-or-None)` | DTO interno exacto; BOOL nativo no-cero se normaliza a bool exacto por el binder. Un `None` de un double no acredita cierre. |
| `_MemoryOps(allocate, release, copy_in, copy_out)` | DTO interno frozen, cuatro callables confiables; sin DLL/handle API genérica. Los tests CPU aportan implementación propia del mismo seam. |

El seam interno es `_assemble_memory_context(ops: _MemoryOps, *, provenance: str) -> _MemoryContext`. No se exporta a callers del store o CLI. Producción sólo entra por `_new_memory_context`; tests entran por assembly privada con `cpu_double`. La etiqueta provenance no autentica autoridad de archivo: incluso una etiqueta fabricada nunca genera writer.

Las cuatro operaciones del backend tienen firmas cerradas: `allocate(size_bytes)->_AllocResult`, `release(base)->_BoolResult`, `copy_in(address,data)->None`, `copy_out(address,length)->bytes`. Sus scalars sólo cruzan código privado confiable bajo el lock. El double opera sobre su propio diccionario de bloques; jamás dereferencia addresses ficticios con ctypes.

El backend nativo expone `_new_native_memory_backend()` sólo a la fachada. No entrega DLLs/bindings como DTO de usuario. Una futura adquisición de archivo tendrá factory y registro diferentes. No aceptará `_MemoryContext` como RootContext, ni tratará un backend CPU como adquisición nativa.

### 4.3 Gate de plataforma, ABI y DLLs antes de adquirir recursos

La fachada usa sólo biblioteca estándar pura para import. El gate exige simultáneamente `os.name=='nt'`, `sys.platform=='win32'`, `sys.maxsize==2^63-1` y `platform.machine().casefold()` en `{'amd64','x86_64'}`. Luego importa el módulo ABI y verifica punteros/SIZE_T/WCHAR. El perfil es Windows AMD64; ARM64/32bits y valores ambiguos rechazan antes de ctypes/DLLs.

Esos valores de plataforma son gates conservadores del contexto confiable, no autenticadores frente a código hostil en el mismo proceso. La comprobación ctypes posterior confirma tamaños. La implementación no promete una frontera de sandbox Python ni resistencia al controller/deployer malicioso.

El archivo ABI tampoco carga DLLs al importarse. Su factory importa ctypes tras su propio gate duplicado de plataforma, construye estructuras y valida tamaños/offsets. Usa WinDLL de DLLs del sistema con `use_last_error=True`, `argtypes/restype` explícitos y sin rutas del caller. No instala SDK, paquetes o DLLs.

| Tipo ABI x64 | Representación exacta y validación |
|---|---|
| HANDLE/PVOID/PWSTR | `c_void_p`, 8 bytes; PWSTR es dirección del array WCHAR retenido, no conversión a string Python |
| NTSTATUS/LONG/BOOL | `c_int32`, 4 bytes; no usar `c_long` dependiente de plataforma |
| ULONG/DWORD/ACCESS_MASK | `c_uint32`, 4 bytes |
| USHORT/WCHAR | `c_uint16`, 2 bytes; arrays UTF16 explícitos cuando se construya adquisición |
| ULONG_PTR/SIZE_T | `c_size_t`, 8 bytes |
| LARGE_INTEGER | `c_int64`, 8 bytes, offset explícito; no sentinels negativos de append/current-position |
| UNICODE_STRING | Length:uint16@0, MaximumLength:uint16@2, Buffer:pointer@8; tamaño16/alineación8 |
| OBJECT_ATTRIBUTES | Length:uint32@0, RootDirectory:pointer@8, ObjectName:pointer@16, Attributes:uint32@24, SecurityDescriptor:pointer@32, SecurityQualityOfService:pointer@40; tamaño48/alineación8 |
| IO_STATUS_BLOCK | Unión Status:int32/Pointer:pointer@0, Information:size_t@8; unión8, estructura16/alineación8 |

No `_pack_` artificial ni structs compartidos con U2. El binder registra su copia de firmas cerradas. Símbolo ausente, ancho u offset distinto produce ABI_UNACCREDITED antes de VirtualAlloc o adquisición futura. No se usan tipos del backend Linux para acreditar Windows.

| Binding K1, sólo fijar firma salvo memoria | argtypes → restype |
|---|---|
| VirtualAlloc | `(PVOID,SIZE_T,ULONG,ULONG) -> PVOID` |
| VirtualFree | `(PVOID,SIZE_T,ULONG) -> BOOL` |
| CloseHandle / FlushFileBuffers | `(HANDLE) -> BOOL`; no llamadas K1 |
| NtCreateFile | `(HANDLE*,ACCESS_MASK,OBJECT_ATTRIBUTES*,IOSB*,LARGE_INTEGER*,ULONG,ULONG,ULONG,ULONG,PVOID,ULONG) -> NTSTATUS`; no llamada K1 |
| NtReadFile / NtWriteFile | `(HANDLE,HANDLE,PVOID,PVOID,IOSB*,PVOID,ULONG,LARGE_INTEGER*,ULONG*) -> NTSTATUS`; no llamadas K1 |

VirtualAlloc usa addressNULL, size calculado, `MEM_RESERVE|MEM_COMMIT=0x3000` y `PAGE_READWRITE=0x4`. VirtualFree usa base original, size0 y `MEM_RELEASE=0x8000`. Captura last_error inmediatamente ante NULL/FALSE, antes de otras llamadas, logs o liberación del lock. El binder normaliza NULL/0 a `_AllocResult(None,error)`; éxito lleva `win32_error=None`, nunca error residual.

K1 no agrega query/admisión por tener firmas de create/read/write. K2/K3 fijarán todos sus bindings adicionales antes de sus propias adquisiciones. NtQueryInformationFile/NtQueryVolumeInformationFile mantienen las firmas aceptadas G2 y sus exact counts; no se recuerdan a ciegas o cambian por conveniencia.

### 4.4 Longitudes, alineación, cuotas y overflow

La alineación K1 es potencia de dos, 512..65536 bytes, tipo int exacto. El caller puede elegir ese valor para memoria; todavía no es B operativo. Sólo WriterGeometry acreditada elegirá B del archivo más adelante.

`length` es int exacto, positivo y múltiplo de alignment. `MAX_ARENA_BYTES=1048576+65536=1114112`. Cubre PREPARE máximo U1 y consultas acotadas, sin reservar el journal completo. Lectura futura completa agrega chunks a bytes; no crea un mapping del archivo.

Cada contexto admite como máximo ocho arenas cargadas a cuota: vivas, en adquisición o retenidas por incertidumbre. Cada arena carga longitud lógica `n` y bytes solicitados `r=n+B-1`, incluido el padding.

El total lógico es `sum(n)` y se limita a `8*MAX_ARENA_BYTES=8912896`. La cuota solicitada es `sum(r)` y se limita a `8*(MAX_ARENA_BYTES+65535)=9437176`. `quota_accounting=requested_bytes_including_padding`: contabiliza exactamente el size pedido al backend, sin redondeo OS. No es una cota de memoria física, reserva/commit virtual real o consumo total del proceso.

Bajo el mismo `context.RLock` de §4.5, la admisión valida tipos, alineación, longitud y overflow antes del backend. Calcula `r` con `_checked_reservation_size`; luego exige simultáneamente `arena_count<8`, `n<=8912896-logical_bytes` y `r<=9437176-requested_bytes`. Los contadores representan las cargas pendientes y retenidas; permanecen dentro de sus límites. Un incumplimiento rechaza con ARENA_LIMIT y backend calls0. Antes de entered registra la carga provisional `(1,n,r)` y el call record. El rollback acreditado devuelve esa misma carga; nunca sustituye `r` por un tamaño redondeado. No recupera cuotas uncertain hasta cierre acreditado o retirada real, conforme a §4.6.

| Ejemplo aritmético de cuota, no ejecución nativa | Resultado |
|---|---|
| Una arena máxima: `n=1114112`, `B=65536` | `r=1114112+65536-1=1179647`; carga lógica1114112 y solicitada1179647 |
| Ocho arenas máximas | `8*n=8912896`; `8*r=9437176`; ambas cuotas exactas y count8 |
| Novena arena con `n=512`, `B=512` | `r=1023`; rechaza antes del backend por count y cuota lógica/solicitada |
| Supuesto ilustrativo de página4096 | `ceil(1179647/4096)*4096=1179648`; ocho tamaños redondeados suman9437184, ocho bytes más que la cuota solicitada |

Microsoft documenta el redondeo de dwSize a páginas con addressNULL en [VirtualAlloc](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc). Página4096 es un supuesto aritmético, no una observación del host. El ejemplo no mide asignación OS, memoria física o residencia y no fija una cota física. El limiter sigue usando `sum(r)`; no consulta ni contabiliza páginas del OS.

La helper pura `_checked_reservation_size(length,alignment,size_t_max)` comprueba overflow antes de policy-limit. El backend nativo fija size_t_max=2^64-1; no es parámetro de API del caller. Los tests pueden pasar límites pequeños a esa helper sin reservar memoria.

Solicita al backend exactamente `r=n+B-1` bytes, con suma validada y cargada a la cuota solicitada. Tras retorno no-NULL comprueba base int exacto, `0<base<=SIZE_T_MAX`, y `base+r<=SIZE_T_MAX`. Calcula dirección alineada `a=(base+B-1)&~(B-1)` con suma validada. Comprueba `a>=base`, `a+n<=base+r` y `a%B==0`. Ninguna cifra inválida llega a copy o free sobre address inventado.

Si un double retorna una base/rango imposible, el resultado es RESOURCE_UNKNOWN y conserva custody; no VirtualFree sobre el scalar inválido. Un native retorno acreditado seguido de fallo propio de registro necesita rollback según §4.6. No se presupone allocator reuse ni page alignment suficiente para B65536.

Offsets y longitudes de copia son int exactos no-negativos. Se comprueba `offset<=n` y `length<=n-offset`; nunca sumar sin validar. Copia vacía válida sólo dentro de 0..n. `_arena_copy_in` exige bytes exactos, rechaza bytearray/memoryview/subclass y objetos con conversión arbitraria. `_arena_copy_out` exige resultado bytes exactos de longitud pedida.

Para I/O posterior: ULONG length<=2^32-1 y LARGE_INTEGER offset>=0; `offset+length<=2^63-1`. Offset, address y length deben ser múltiplos del B acreditado y rango dentro de EOF/capacidad autorizados. K1 no ejecuta esa I/O ni emite WriterGeometry.

### 4.5 Ownership, registro, locks y lifetime

| Registro privado fuerte | Contenido y duración |
|---|---|
| `_LIVE_MEMORY_CONTEXTS` | Objeto contexto, pid de creación, nonce interno, backend, estado y RLock; antes de primera llamada potencialmente adquisitiva |
| `context.allocations` | Capability por identidad, `_AllocationRecord`, base/rango solicitado, length/B, carga `(1,n,r)` de §4.4, estado y último CloseOutcome; registro antes de publicar capability |
| `context.inflight` | `_MemoryCallRecord` preinsertado, operación, argumentos fuertes, carga provisional `(1,n,r)` cuando alloc, retorno cuando conocido y relación con arena; cubre llamada y reconocimiento/registro |
| `_QUARANTINED_MEMORY_CONTEXTS` | Referencias fuertes a contextos/call records/arenas inciertos hasta terminación/reap real del proceso; nunca weakref o GC cleanup |

El registro usa referencias de objeto, no IDs reciclables. Un owner pide pid actual al validar cada operación. Una capability trasladada a otro proceso o ligada a otro contexto rechaza antes del backend. Los nonces nunca salen como credencial pública.

El kernel mantiene `_KERNEL_POISONED` por proceso y lo consulta bajo la guardia global antes de registrar un contexto y antes de cada llamada de backend. K2+ deben respetar ese gate al adquirir/operar archivos; no basta revisar un owner recién creado. No comparte ni restablece los globals de U2. Los estados readonly aceptados no conceden autoridad para limpiar una cuarentena del kernel.

Cuando el gate global está poisoned, las capabilities restantes pierden autoridad efectiva, aunque su registro conserve el estado previo para diagnóstico. Copy/allocate rechazan OWNER_RETIRE_REQUIRED; close reserva/devuelve unknown sin llamada nativa. ArenaInfo informa unknown para recursos que no estaban ya closed. Ningún thread revalida únicamente su contexto y omite el gate global.

Orden de locks: guardia global del registro para localizar/pinear contexto; se suelta antes de adquirir context.RLock. Después se revalida objeto/estado/pid bajo RLock. Mutaciones globales hechas bajo RLock usan la guardia global sin esperar otro context lock. Ningún camino mantiene guardia global esperando un RLock.

Todas las operaciones de una arena y cierre del contexto se serializan con ese RLock. El GIL no es un lock de ownership: ctypes puede ejecutar fuera de él. No se ejecutan callbacks del caller, logging extensible, herramientas o código de lifecycle bajo el lock. Sólo el backend confiable o double privado controla el seam.

Mientras la llamada está entered, arrays, buffers, argumentos y retorno quedan retenidos hasta reconocimiento completo. La entrada en custodia precede la llamada; un `finally` nunca libera por retorno al stack. Una copia recibida ya acreditada permanece válida tras cierre porque es bytes independiente.

Un thread concurrente sólo observa el estado revalidado tras adquirir el lock. Si cierre ganó, copy rechaza sin backend. Si copy ganó, cierre espera su fin. Ante interrupción después del retorno antes del registro, call record y owner quedan globalmente retenidos, aunque el retorno no haya llegado a guardarse. La retirada del proceso cubre esa adquisición desconocida.

### 4.6 Rollback, poison y close una sola vez

| Situación | Estado y acción cerrada |
|---|---|
| Error de tipos/rango/plataforma/ABI/cuota pre-entry | Rejected, backend calls0; no revocar arenas sanas |
| VirtualAlloc retorna NULL acreditado y error capturado | ALLOCATION_FAILED, no arena; devuelve carga provisional `(1,n,r)` de §4.4; contexto puede seguir vivo |
| Base nativa válida retenida, fallo ordinario de registrar capability | Revocar reserva; intentar VirtualFree base una sola vez si completion está totalmente acreditada; preservar causa primaria y cleanup separado |
| Excepción/interrupción dentro de alloc/copy/free o reconocimiento ambiguo | RESOURCE_UNKNOWN, poison del contexto, revocar toda capacidad antes de exponer error; retener call records/arenas/backend |
| Resultado del double con tipo/longitud inválidos | Completion no acreditada; misma custody/poison. No inferir éxito desde truthiness o None |
| `_close_arena` normal | Reservar CloseOutcome unknown; marcar revoked; retirar dirección de autoridad; registrar call record; VirtualFree(base,0,MEM_RELEASE) una vez |
| VirtualFree TRUE acreditado y reconocimiento completo | Estado closed, outcome closed; devuelve carga registrada `(1,n,r)` de §4.4; ninguna segunda llamada al scalar |
| VirtualFree FALSE/excepción o interrupción después de TRUE antes de registro | Outcome unknown, poison y custodia fuerte; jamás retry. Incluso si el OS pudo liberar, address antiguo no se reutiliza |
| Cierre con contexto poisoned o llamada incierta | Revocar y devolver unknown estable; no VirtualFree ni CloseHandle; conservar hasta retirada del proceso |
| Close repetido/desde threads rivales | Devolver outcome reservado/final del primer intento; backend-call count total<=1 |

CloseOutcome no se cambia a closed por timeout, conteo global o desaparición de referencia. Un contexto con cierre sano se marca closed y deja su registro live; tombstones locales conservan outcomes mientras exista la capability. Una llamada posterior sobre el objeto cerrado no registra una nueva adquisición.

`_close_memory_context` reserva unknown agregado y revoca el contexto primero. Libera sólo arenas con ownership y ausencia de incertidumbre acreditadas. Si un cierre falla, deja de liberar los restantes: el contexto está poisoned. Preserva resultados closed previos y las causas individuales. Una segunda llamada no repite ningún free.

No destructor, atexit, finalizer o context manager silencioso puede declarar cleanup. Si se añade context manager en otra unidad, debe mantener error primario y reportar cleanup unknown separado. K1 utiliza cierre explícito; no inventa una recuperación automática.

La cuarentena bloquea nuevas reservas nativas del kernel en ese proceso, incluso creando otro contexto. Un supervisor confiable tendrá que terminar/reap al owner antes de recuperación. K1 registra esa necesidad y no mata procesos ni añade IPC/servicio. No implementa release-after-dead-pid en el mismo proceso.

Los casos CPU uncertain usan instancia privada de módulo/registro por caso y sólo backend CPU. No restauran un registro nativo poisoned para convertirlo en sano. Los tests no tienen API de reset de producción ni retiran recursos native inciertos con monkeypatch. Una cuarentena nativa real exige terminar/reap al proceso conforme a la release futura.

Para K2+ la misma disciplina cubrirá STATUS_PENDING=0x103, ERROR_IO_PENDING=997, IOSB inconsistente y éxito de NtCreateFile antes del registro. No wait/cancel/retry rescata esa autoridad en este perfil. El patrón experimental con WaitForSingleObject no se traslada al producto.

CloseHandle futuro reserva outcome, revoca primero y usa scalar registrado propio una sola vez. Rechaza NULL, bool, negativos, ancho inválido y valores pseudo del rango alto reservado. Política conservadora propuesta: `0<h<2^64-16`, int exacto, más origen registrado. Un scalar que pase ese rango aún no acredita ownership.

### 4.7 Errores sanitizados y evidencia que puede salir

`KernelMemoryError` es la única base privada K1. Lleva `diagnostic:FailureDiagnostic` frozen y `cleanup:CloseOutcome-or-None`. Su texto contiene sólo code/operation cerrados. No usa `str(error)`, repr del caller, nombre de clase de excepción arbitraria o traceback como diagnóstico exportable.

| Código cerrado K1 | Operaciones permitidas |
|---|---|
| PLATFORM_UNSUPPORTED | context |
| ABI_UNACCREDITED | bind |
| CAPABILITY_INVALID / CAPABILITY_REVOKED / OWNER_MISMATCH | allocate/info/copy_in/copy_out/close/context_close |
| INTEGER_INVALID / RANGE_INVALID / ALIGNMENT_INVALID / OVERFLOW / ARENA_LIMIT | allocate/copy_in/copy_out |
| ALLOCATION_FAILED | allocate |
| RESOURCE_UNKNOWN / OWNER_RETIRE_REQUIRED | allocate/copy_in/copy_out/close/context_close |

Excepciones de backend se retienen sólo dentro de custody protegida. El error exterior suprime chaining público y no publica HANDLE, base, address, SID, path, nonce o backend. `FailureDiagnostic.ntstatus` es None en operaciones K1 de memoria; Win32 error se valida uint32 cuando fue capturado inmediatamente. No se inventa error0 como éxito.

La causa primaria siempre queda primera. Un rollback/free incierto añade cleanup; no sustituye el fallo original ni acredita que la operación principal no ocurrió. Las pruebas verifican que repr/error/DTO no contienen sentinels secretos aportados por el double.

### 4.8 Ejemplos válidos, negativos y controles antes de RED

Son secuencias de interfaz propuestas, no código implementado o ejecutado.

| Caso | Entrada/secuencia y resultado esperado | Control causal |
|---|---|---|
| Memoria mínima | Contexto propio; allocate length512/alignment512; copy_in offset0 bytes512; copy_out512; close | Bytes exactos nuevos y un solo free de base original, no address alineado |
| Sector grande | length131072/alignment65536; base del double no alineada65536 | Intervalo alineado completo dentro del rango solicitado196607; prueba positiva aunque base%B!=0 |
| PREPARE máximo | length1114112/alignment65536 | Se admite; longitud1114112+65536 rechaza antes de alloc |
| Copia vacía | offset==arena.length, data b'' / length0 | Permitida sin acceso fuera de rango; offset==n+1 rechaza incluso length0 |
| Capability falsa | dict, -1, 0, True, ctypes pointer, subclass o object.__new__(AlignedArena) | Backend calls0; objeto auténtico paralelo sí funciona |
| Owner distinto | ArenaA con contextB, o pid observado distinto al emisor | OWNER_MISMATCH y calls0; mismo objeto/origen/pid pasa |
| Tipos/rango | length=True, alignment513, length513/B512, offset-1, bytearray o memoryview | Error específico y calls0; controles int exacto/bytes exactos pasan |
| Overflow | Helper con n=SIZE_T_MAX, B512; helper con límite reducido controlado | OVERFLOW sin alloc; n=512/B512/límite1024 produce1023 |
| Lifetime de copia | copy_out; modificar arena; cerrar; conservar primera copia | Primera copia inmutable e idéntica; no vista a memoria liberada |
| Fallo conocido alloc | NULL y error8/1455 capturado por double | No capability ni free; siguiente alloc sano admitido |
| Register window | Double/fault privado interrumpe después retorno válido antes de registrar | Custody fuerte, poison; no free incierto ni nueva reserva |
| Cierre defectuoso | FALSE, None, excepción, interrupción antes/después de TRUE | Un intento máximo; outcome unknown repetido; todos los siblings revocados |
| Concurrencia | Dos threads close, y copy vs close bajo barrera privada de test | Orden registrado, count<=1 y cero copy tras revoked; sin sleeps como causalidad |
| Import Linux | Import fachada y factory nativa con import de ctypes/DLL bloqueado y registrado | PLATFORM_UNSUPPORTED, import de ctypes0/DLL0/alloc0; CPU double separado sí prueba lógica |

### 4.9 Matriz de criterios unitarios y límites de verificación

Cada criterio debe tener RED causal antes de su comportamiento. Se permiten asserts privados del registro para ownership y counts. No se agrega ahora harness, tests ejecutables o experimental native code.

| ID K1 | Criterio verificable futuro | Entorno/control |
|---|---|---|
| K1-01 | Import unsupported sin ctypes/DLL; 32bits/ARM64/arquitectura ambigua rechazan | Linux negativo real e inputs CPU controlados, no Linux fingido Windows positivo |
| K1-02 | Todos widths, sizes, offsets y argtypes/restype de §4.3 validados antes recursos | Windows ctypes real; fake DLLs privados para símbolo ausente/firma incorrecta; alloc counters0 |
| K1-03 | Reserva/alineación/bounds, count8, `sum(n)`/`sum(r)` y overflow exactos, sin fallback | CPU doubles para base desalineada, límites, retorno inválido y accounting solicitado de §4.4; no cota OS/física |
| K1-04 | Capabilities exactas sólo del registro/owner/pid; nada fabrica autoridad de archivo | CPU positivos/negativos emparejados; registry snapshots y calls0 |
| K1-05 | Copias byte exactas, rangos, independencia/lifetime y zero-length | CPU doubles y Windows memoria propia sin archivos |
| K1-06 | Return-to-register window mantiene custody en todos sus cortes | Fault hooks privados definidos en tests y monkeypatch de seams internos; sin hooks públicos/fake grants |
| K1-07 | Revocation-before-free; outcomes idempotentes; FALSE/None/excepción/interrupción no retry | CPU conteos1 y orden, siblings revocados/quarantine fuerte; control TRUE sano |
| K1-08 | Context close inverso, cuotas rollback y primary/cleanup separados | CPU con dos/tres reservas; un fallo intermedio deja restantes retenidos |
| K1-09 | Threads copy/close serializados por lock real; proceso distinto rechazado | CPU threads y barreras deterministas; pid override privado readonly, no nuevo child harness |
| K1-10 | Diagnósticos frozen sin scalars, buffers o causas arbitrarias | CPU sentinels secretos y tipos inválidos; repr/error/export cerrado |
| K1-11 | VirtualAlloc real, B512/4096/65536, copias/close exactos sobre memoria exclusivamente propia | Windows nativo liberado aparte por ROOT; sin NtCreateFile, flush, GPU/admin/ACL/archivo |
| K1-12 | Preimágenes U1/U2 intactas y whole>=80% por archivo nuevo | Hash guards, cobertura oficial de ambas fuentes sin omit/exclude/pragmas; revisión fresca y QA independiente |

La cobertura whole incluye cada archivo completo `storage_journal_windows_io.py` y `storage_journal_windows_abi.py`, no sólo líneas del diff. Cada uno alcanza >=80% de líneas; se informa también ramas. No se maquilla un archivo por el promedio del otro. Si Linux no ejecuta el binder, se informa su limitación y se combina evidencia oficial Windows/Linux autenticada por mismo SHA. No se convierte skip native en pass.

Windows evalúa binder/copia real y Linux gate negativo/lógica CPU. La QA independiente debe distinguir los nodos y sus fuentes. No se necesita un test de archivo, flush o full-chain para afirmar aceptación de K1, porque K1 no entrega esas propiedades. Tampoco K1 aceptado acredita T05 o M1.

### 4.10 Unidades posteriores obligatorias y sus calling seams

Estos nombres ordenan las fronteras, sin estimar horas ni sustituir el ledger. ROOT/planner liberarán cada unidad con su contrato antes del RED. Ninguna se considera realizada por esta propuesta.

| Unidad futura | Seam cerrado requerido antes de liberar | Prerrequisitos/resultado y frontera |
|---|---|---|
| K2 adquisición propia | `_open_owned_component(owner,parent,name,profile,disposition,descriptor)` privado; profiles nominales parent/read/writer/create, sin masks arbitrarios | Call arena con UTF16/UNICODE_STRING/OBJECT_ATTRIBUTES/SIDs/ACL/descriptor/IOSB/output; registro pre-entry y éxito antes registro; FILE_OPEN/OPENED o CREATE/CREATED exactos; no root trust por path |
| K3 metadata/mode/streams/G2 | `_inspect_owned_file(acquisition)` y `_derive_owned_geometry(acquisition,observation)` | Queries del mismo handle, identity/regular/link/delete/attrs/NTFS/EOF y parser streams limitado1MiB; modo real; copia G2 pura existente, no envolver WriterLease como `_ObservedHandle` |
| K4 ancla y S1 full-chain | `admit_root(deployer_authority,project_components)`; emisión privada RootContext/ChainLease sólo tras todos los padres | Ancla real Windows/system-root exception/principal ratificado, no JSON/hash; S1 actual por cada handle y lock/custodia completa. Host outsider MODIFY conserva SECURITY_UNACCREDITED |
| K5 I/O exacto propio | `_read_exact`, `_write_exact`, `_flush_exact` sobre acquisition/WriterGeometry/AlignedArena nominales propias | Largo/offset/address B y conteos exactos, barriers mismo handle, no retries short/PENDING ni seek/append; fixture probe sólo scope ROOT separado sin promoción de trust |
| ST1 store físico | `create_new`, `open_read`, `open_writer` del contrato ADR-0081 | Header y 64slots U1, ceros reales, capacidad exacta, EOF/allocation/flush/relectura; seed/final existentes conflicto y conservación; exclusión read/share y writer/share0 reales |
| ST2 store CAS/ACK/replay | `writer.commit(expected_token,request,snapshot)` y `recover_ack(request)` | Token completo, bytes/request anteriores, PREPARE+flush1+read, COMMIT+flush2+fullread/revalidate antes ACK; replay histórico con head actual distinto, cero slot/efecto nuevo |
| ST3 recovery causal | Clasificación C0–C7 del store y protocolo separado para cola bloqueada | Kill/reap real cuando liberado; conservar incomplete/corrupt sin prefijo operativo. Vincular otro journal sin overwrite requiere concreción propia; rechazo solo no cumple recovery final |
| L1 bootstrap legacy | `bootstrap_published` y snapshot/identidades ratificados; ReceiptLease/PublishedDiskBinding retenidos | Seed exacto v1 y generación inicial, no adoptar SMOKE/path/hash; firmas de lectores aceptados preservadas |
| L2 lifecycle/admisión | publish/attach/validate/quiesce/detach/reconcile del controller, requests correlacionados | Intención ACK antes efecto y completion ACK antes éxito; retire writers JSON por ruta tras wiring revisado; epochs actuales, namespace/consumidores reales y quiesce/flush exactos |
| E1 aceptación persistente | Cadena provisionada S1 y VHDX/ext4/UUID/namespace/restart/backup/E2E/manuales | Gates físicos elevados cuando autorizados, producción Docker y todo dentro del proyecto; reinicio/powerloss distinguidos de subprocess y dobles CPU |

ST1–ST3 son etiquetas provisionales de fronteras del store. La política estricta S1 permanece la del ADR-0076.

Para K2 el contrato cerrado debe identificar cómo acquire root sin parent nominal y cómo registrar output antes de publicar adquisición. La receta de create descriptor sólo permite owner principal y trustees ratificados. No se libera esa API por escribir su nombre aquí.

Para K3 el kernel ejecuta sus queries propias. Puede entregar `MetadataObservation`/`GeometryObservation` copiadas a `derive_geometry_candidate` puro. No llama `read_handle_geometry` con writer, no usa `_BorrowedDirectory` fabricado y no comparte `_RETAINED` U2. La evidencia de origen queda en el registro del kernel; un B candidato suministrado por caller no se transforma en WriterGeometry.

K4 conserva adquisición de root→proyecto→data→_storage; todas deben pasar S1 vigente. Dataset nuevo temporal, descriptor closed del leaf y un testigo kernel positivo siguen parciales cuando fallan ancestros. RootContext sólo nace de deployer actual ratificado y chain acreditada, no de un test hook `trusted=True`.

K5 tendrá perfil `GatedNativeProbe` con scope ROOT nominal distinto de RootContext/WriterLease. No se añade bypass dentro del store. Sus pruebas de flush exacto nuevas no borrarán los originales experimentales con exit1. No existe probe→ChainLease o probe→ACK de producto.

La operación que recibe ACK perdido hace replay del request exacto después de reacreditar todas las capacidades. Un commit sealed con cleanup unknown conserva ambas dimensiones. No repite efecto porque close falló. Bootstrap físico y legacy son categorías separadas; lifecycle no se habilita ampliando enums U1.

## 5. Impacto en módulos y ficheros

| Ruta respecto al repo | Cambio propuesto y ownership de implementación futuro | Tipo |
|---|---|---|
| `scripts/storage_journal_windows_io.py` | K1 fachada, registro/arena/errores; futuro kernel acquisitions/I/O bajo releases independientes | Nuevo propuesto, owner implementer K1 fresco cuando ROOT libere |
| `scripts/storage_journal_windows_abi.py` | C2 binding y structs ABI propios; ninguna autoridad o adquisición de archivo | Nuevo propuesto, mismo owner K1 para seam no concurrente |
| `tests/test_storage_journal_windows_io.py` | Tests K1 CPU y memoria propia Windows sólo tras release/TDD; controles causales | Nuevo propuesto, mismo owner K1; no escrito por arquitecto |
| `tests/test_storage_journal_windows_abi.py` | Binder/widths/offsets/errores Windows y negativo unsupported | Nuevo propuesto, mismo owner K1; no escrito por arquitecto |
| `scripts/storage_journal.py`, `tests/test_storage_journal.py` | U1 intacto; no wire/layout/repair nuevo | Existentes preservados, fuera ownership K1 |
| `scripts/storage_journal_windows.py`, `tests/test_storage_journal_windows.py` | U2 accepted íntegro; copiar patrones, no compartir capability/global | Existentes preservados, fuera ownership K1 |
| `scripts/storage_journal_store.py`, `tests/test_storage_journal_store.py` | Store trust/CAS/ACK/replay/physical bootstrap futuras | Nuevos propuestos en contrato aceptado, no release K1 |
| `scripts/storage_lifecycle.py` | Controller y admisión futura con concreciones propias | Nuevo propuesto, no release K1 |
| `scripts/storage_receipt_store.py`, `scripts/storage_operator.py` | Lectores readonly aceptados; no transformar en writer | Existentes referenciados por contrato padre, fuera ownership |
| `scripts/storage_offline.py`, `scripts/storage_publish.py`, `scripts/storage_attach.py` | Wiring al controller futuro y retirada coordinada de writers JSON | Existentes, fuera ownership y release actual |
| `packages/storage-guard/studio_storage_guard/receipt.py` | Payload v1 preservado | Existente snapshot, sin cambios |
| `.cache/dev-cycle/m1/storage-journal-kernel-contract-fix1-20261011/snapshot/docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md` | Propuesta privada FIX1 del accounting solicitado | Única escritura documental de diseño actual |

La existencia de auxiliares fuera de las17fuentes deriva del contrato padre aceptado. Esta pasada no los revalida como producto ni les atribuye evidencias nuevas. ROOT verificará sus preimágenes antes de cualquier brief que los toque.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Assembly CPU confundida con authority native | Evitable | Writer falso | K1 sólo memoria; registros de adquisición/trust separados, factories nominales futuras y tests negativos |
| Excepción entre return y registro pierde base | Posible | Reserva incierta o reuse peligroso | Registro entered previo, custody fuerte incluso sin scalar conocido, poison y retirada del proceso |
| Free falla o se interrumpe tras éxito | Posible | Doble free/reuse | Outcome reservado, revoked-before-call, no retry y quarantine |
| DLL binding firmado pero usado por caller | Evitable | Create/write fuera de authority | No exportar DLL, función o call-arbitrary; K1 invoca sólo alloc/free/copias |
| Lock serializa sólo por GIL | Evitable | Use-after-free concurrente | RLock real y barreras causales CPU; orden global/context sin inversión |
| Cuotas/límites insuficientes para PREPARE | Evitable | Implementer cambia política a ciegas | Máximo deriva de U1+65536; comparar encode_prepare real antes release K1 |
| Cuota solicitada confundida con reserva/commit OS o memoria física | Identificado en QA1 | Cota falsa antes de RED | FIX1 distingue `sum(n)`/`sum(r)` del redondeo OS; revisión2 A/B y QA2 pendientes; sin medición nativa ni cota física |
| Factories unsupported cargan ctypes | Evitable | Linux negativo engañoso | Import facade puro y gate antes native module/ctypes/DLL; loader denegado controlado |
| Ancestros outsiders bloquean producción | Ya documentado | Full-chain sin positivo | Rechazo S1 íntegro; provisión ratificada separada, no modificar ACL ni promover dataset |
| Cobertura sólo promedio/gate diff | Evitable | Binding/custody ocultos | Whole por archivo>=80 sin exclusiones; datos oficiales por SHA/plataforma |
| Experimento funcional confundido con powerloss/no-leak | Evitable | Aceptación falsa | Conservar exit1/deltas y separar K1/native kernel/full-chain/ACK/host crash |
| Cola bloqueada se presenta como recovery completo | Riesgo conocido | Objetivo T05 incumplido | Protocolo causal independiente obligatorio antes de reanudación final |

Esta organización añade verificación whole de un segundo archivo; no recalcula horas/euros. El planner/evaluator decidirán si ese cambio relativo exige actualizar la evaluación. K1 no instala herramientas ni ejecuta tests nativos con esta entrega.

## 7. Preguntas abiertas

| Puerta | Decisión pendiente y responsable | Qué bloquea |
|---|---|---|
| Pre-RED K1 | C2 elegida; ROOT mantiene §4.1–4.9, APIs/DTO/tipos exactos, límites y fuentes; FIX1 de cuota solicitada requiere revisión2 A/B, QA2 y adopción | No liberar implementación ni RED antes de esas puertas |
| Release K1 | Cuatro rutas K1 mantenidas por ROOT; snapshot/brief, owner fresco y release de memoria propia Windows pendientes | No archivo/I/O/probe/RootContext/grant por esa release |
| Revisión K1 | ROOT despacha revisión fresca adecuada y QA independiente tras TDD con cobertura whole | Ninguna aceptación por resultado del implementer o por esta prosa |
| K2/K3/K4/K5 | ROOT cierra adquisición de ancla, calling arenas, bindings/query/mode/streams, factories S1 y I/O propios | No inferir esas interfaces desde nombres propuestos o U2 readonly |
| Full-chain positiva | ROOT ratifica provision/deployer/principal/cadena real compatible S1 | Leaf privado positivo no abre gate; remediación ACL separada |
| Recovery causal | Contrato de autoridad/vinculación entre journals para cola bloqueada | Clasificación/rechazo sola no satisface recovery persistente final |
| Bootstrap/lifecycle/ext4 | Releases separadas con bindings existentes, intención/completion/admisión y gates físicos reales | K1/store parcial no cierra T05/M1 |
| Registro documental | ROOT decide dónde enlazar concreción ratificada en documentación vigente | No nuevo número ADR asignado ni cambios al índice por este actor |

No se propone cambiar O2/S1/G2 o la Constitución. ADR-0081 sigue siendo la decisión existente. Si ROOT detecta que una concreción exige cambiar una decisión, deberá reservar número y proponer ADR explícito antes del cambio; este actor no reserva, sobrescribe o escribe un ADR nuevo.

El siguiente handoff es a ROOT para revisión2 A/B, QA2 documental y adopción de FIX1 de esta concreción elegida. Después ROOT podrá liberar K1 a implementer fresco con contrato cerrado. No es handoff directo a código o planner ni aceptación técnica de una unidad, T05 o M1.

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-11 | Propuesta privada C1/C2; contrato K1 completo y fronteras posteriores obligatorias, sin producto, tests o native experiments |
| 2026-10-11 | ROOT elige C2 bajo delegación expresa; original byte exacto preservado; contratos y cuotas intactos; revisión/QA/adopción pendientes |
| 2026-10-11 | FIX1 ante gap nuevo Important confirmado por ROOT/QA1: cuota de bytes solicitados `r=n+B-1`; límites8912896/9437176 y count8 preservados. Ejemplo de redondeo OS sin medición/cota física; revisión2/QA2/adopción pendientes |


## Acta ROOT de adopción del contrato K1 — 2026-10-11T17:15:43.986178+00:00

C2 y el contrato pre-RED quedan ratificados e incorporados tras revisión2 A/B limpia y QA2 independiente 91/91 controles documentales, qa-gate oficial0. QA1 roja66PASS1FAIL íntegra: QA1-01 corregido en fuente. Estado y mensajes anteriores del actor son históricos; esta acta fija la adopción documental actual. La cuota contabiliza bytes solicitados r=n+B-1, no reserva físicaOS. Esta adopción no acredita runtime K1, T05/M1, full-chain/store/ACK/bootstrap/lifecycle/recovery/ext4/E2E/manuales. ROOT libera implementación K1 sólo cuatro fuentes nuevas ABI/memoria/tests, TDD causal y cobertura whole mínimo80porarchivo antes revisión/QA de producto. Efectos permitidos: memoria volátil del hijo Windows propio, VirtualAlloc/VirtualFree y copias propias; no archivos/NTCreate/Read/Write/Flush, ACL/admin, RootContext/grants, GPU/servicios o producción. QA2 publicó su informe directamente en el destino canónico, contrario al aislamiento snapshot indicado en el brief. ROOT autenticó y conserva esos bytes por SHA, registra el desvío de colocación sin atribuirlo a un CAS ROOT previo. No cambió fuentes normativas ni ledger.
