---
design: storage-nt-geometry-u2b2
titulo: Geometría NT readonly y candidato B sin capacidad de writer
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: spec.md
evaluacion: n/a
plan: improvement-plan.md
adr: ../../decisiones/ADR-0078-geometria-nt-readonly-del-journal.md
opcion_elegida: G2
validada_por: ROOT bajo delegación vigente del propietario
validacion_utc: '2026-10-11T11:43:04.005269+00:00'
validacion_via: elección G2 explícita recibida del orquestador
revision_documental: conforme A+B intento1; QA documental33/33 intento3
adopcion_canonica: ROOT 2026-10-11T12:16:41.617978+00:00
release_implementacion: true
namespace_opciones: geometry-only G1/G2/G3; no cambia O2 durable ni S1 seguridad
recomendada: G2
agente: architect
tier_resuelto: opus
reasoning_resuelto: high
generacion:
  fuente: estimado
  tokens_reales: null
  coste_real_eur: null
  horas_ia_reales: null
  motivo: preparación paralela sin marker propio; ROOT mide su siguiente unidad aparte
---

# Diseño — Geometría NT readonly de M1/T-05/U2b2

> Spec M1 aprobada. Evaluación n/a. Plan M1 existente. ADR-0078 aceptada por ROOT tras revisión y QA documental; implementación aún pendiente.

| | |
|---|---|
| Estado | Aprobado y adoptado por ROOT; revisión A+B conforme con Minor anotado y QA33/33; implementación pendiente |
| Opción elegida | G2 por ROOT bajo delegación vigente del propietario |
| Validación | ROOT, 2026-10-11T11:43:04.005269+00:00; elección explícita G2 |

## 1. Contexto y restricciones

U1 aporta el codec puro `scripts/storage_journal.py`. `JournalLayout.alignment` admite potencias de dos entre512 y65536bytes.
U2a y U2b1 viven en `scripts/storage_journal_windows.py`. Las rutas solicitadas `storage_journal_security.py` y `storage_journal_codec.py` no existen.
U2b1 af192c76519d88e8b1cbd267a8326bf74e54a871dbcd5c0dc5a13a8297e56db4 está aceptada; tests actuales3de1e82 conservan su AST aceptado.
La QA2 pública acredita apertura relativa, metadata y custodia; excluye expresamente geometría. El push67e1f09 y esa aceptación no acreditan U2b2.

ADR-0075 fija **O2 del journal durable**. ADR-0076 fija **S1 de seguridad**. Este diseño no reabre ninguna decisión.
La preparación anterior llamó O2 a la autoridad NT. Aquí G1/G2/G3 nombran exclusivamente alternativas de geometría; tampoco son los gates G1–G8 históricos.

**Restricciones que fijan el espacio de soluciones**

- Sólo consultas readonly sobre una adquisición propia U2b1 existente, síncrona y retenida. Sin apertura directa de device/volumen ni nuevo perfil de derechos.
- Sin writer, store/readview operativa, journal de producto, bootstrap, creación, escritura, flush, ACK, recovery, lifecycle, CLI o validación de cadena S1.
- Sin alterar wire U1, la política S1, ACL existentes, datos, SMOKE, WSL/Docker/GPU, admin o servicios.
- `FileStorageInfo` Win32 no proporciona flags NT. No mezclar APIs, utilizar fallback ni elegir una respuesta para admitir el host.
- M1/T-05 permanecen abiertos. Dos outsiders MODIFY, bootstrap TrustedInstaller y ext4 persistente siguen siendo gates independientes.
- La preparación original sólo modificó documentos privados. ROOT adopta ahora contrato y ADR tras revisión/QA; runtime y tests siguen intactos.

### Fuentes y qué acreditan

Las páginas oficiales se consultaron mediante web el2026-10-11. Copias HTML y SHA256 están en `primary-sources.receipt.json`.
La siguiente tabla separa hechos de Microsoft de decisiones restrictivas propias del proyecto.

| Fuente primaria | Hecho utilizado |
|---|---|
| [NtQueryVolumeInformationFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryvolumeinformationfile) | Cinco argumentos; buffer del caller; Information cuenta bytes escritos; archivo/directorio válido; no class11 sobre device directo |
| [NtQueryInformationFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryinformationfile) | Cinco argumentos; class17 consulta alineación sin acceso adicional específico; Information cuenta bytes escritos |
| [Estructura NT de sectores](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddk/ns-ntddk-_file_fs_sector_size_information) | Siete ULONG, consulta por archivo/directorio; la fila TRIM tiene un nombre repetido en esta DDI |
| [MS-FSCC sectores](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/3e75d97f-1d0b-4e47-b435-73c513837a57) | Flags independientes1/2/4/8 y offset desconocido0xffffffff; no-seek/TRIM no son alineación |
| [Estructura NT de alineación](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddk/ns-ntddk-_file_alignment_information), [MS-FSCC alineación](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/9b0b9971-85aa-4651-8438-f1c4298bcb0d) | Un ULONG y conjunto cerrado de máscaras0,1,3,7,15,31,63,127,255,511 |
| [IO_STATUS_BLOCK](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_io_status_block) | Union Status/Pointer e Information pointer-sized; retorno noPENDING gobierna aunque IOSB.Status difiera |
| [Microsoft Terminal, header fijado](https://github.com/microsoft/terminal/blob/89d82638ab2b01d9d07cd25e36e0374f5eb83c95/src/host/conddkrefs.h) | Enum FileFsSectorSizeInformation=11, línea76; referencia ROOT SHA f87167a3d5fe1a72dbeed57246884327d917cad44d944c90062ba96526515537 |
| [File buffering](https://learn.microsoft.com/en-us/windows/win32/fileio/file-buffering) | Alineación de transferencias/buffers se verifica aparte de obtener información de geometría |
| [FILE_STORAGE_INFO Win32](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_storage_info) | Definición separada; no certifica los bits4/8 observados en su experimento Flags15 |

No se copia código Microsoft/Terminal al runtime ni se instala SDK. Copias primarias sólo documentan la investigación.
La documentación de funciones user-mode nombra Nt; la carga desde `ntdll.dll` continúa siendo binding propuesto que necesita prueba futura.

## 2. Opciones (2-3)

### G1 — Dos consultas NT y copia raw; derivación B aplazada

Completar ABI, lifetime e identidad NT ahora. Devolver únicamente las dos respuestas diferenciadas y metadata antes/después.
El futuro writer necesitaría otra concreción para validar flags/offsets y derivar B. No usaría Win32 como fallback.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: binding NT, arenas y custodia; sin política de derivación |
| Riesgo | Medio: consumidores podrían inventar su propia política; hay que bloquear expresamente esa integración |
| Coste relativo | S ahora, nueva puerta posterior para B |
| Reversibilidad | Alta: añadir derivador puro no cambia respuestas raw |

### G2 — Dos consultas NT y derivador puro de B candidato

Conservar las respuestas raw y completar ahora una política cerrada de tamaños, máscaras, flags y offsets.
Un derivador puro devuelve candidato B o causas bloqueantes. Esa cifra no autoriza I/O ni admite el journal.
El writer futuro reconsulta su propia adquisición y acredita sus buffers, modo y capacidades.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: G1 más política pura cerrada y casos negativos |
| Riesgo | Medio-bajo: hay rechazo conservador de geometrías legítimas no cubiertas; no admite por fallback |
| Coste relativo | M; resuelve la frontera geométrica necesaria antes del writer |
| Reversibilidad | Alta: política versionada local; wire U1 y formato raw no cambian |

### G3 — Mantener diagnóstico Win32 y posponer toda autoridad NT

Preservar el alcance U2b1 y la propuesta previa. No implementar consultas NT ni derivar B desde ellas ahora.
El gate geométrico continúa cerrado hasta otra unidad. Win32 sigue rechazando bits no acreditados por su contrato.

| Criterio | Valoración |
|---|---|
| Complejidad | Baja: sin binding ni contrato NT nuevo |
| Riesgo | Bajo inmediato; alto riesgo de aplazar indefinidamente la dependencia del writer |
| Coste relativo | S ahora; coste posterior sin resolver |
| Reversibilidad | Alta: no introduce nuevas respuestas ni capacidades |

## 3. Criterios de decisión

1. Preservar custodia y rechazo ante incertidumbre antes de ampliar cobertura de hosts.
2. Una sola autoridad geométrica explícita; procedencia NT separada de Win32 y de política S1.
3. Cerrar B antes del RED del componente que lo derive, sin convertirlo en token de writer.
4. Mantener exactamente el wire U1 y separar pruebas puras, doubles de contingencia y futura consulta nativa.
5. Reutilizar la contención U2b1 aceptada; no añadir wait/cancel/retry ni solución experimental de PENDING.
6. Mantener revisión documental, ROOT release, TDD, revisión fresca y QA como puertas sucesivas.

## 4. Recomendación · opción elegida y por qué

**Recomendada: G2.** Cierra la dependencia geométrica del writer con una política comprobable, sin entregar capacidad nativa.
**Opción elegida: G2 por ROOT, 2026-10-11T11:43:04.005269+00:00.** ROOT ejerció la delegación vigente del propietario mediante elección explícita. La opción respeta los criterios1–6. Revisión A+B conforme y QA documental33/33 verificadas; ROOT adopta diseño y ADR. La implementación queda pendiente de su release específico.
Descartadas para esta unidad: G1 aplaza la política B que necesita el writer; G3 aplaza íntegramente la dependencia NT. ROOT eligió G2 para cerrarla conservando raw y custodia, sin capacidad de escritura.
Mezclar respuestas o tomar la que permita pasar no constituye alternativa admisible: pierde procedencia y contradice los criterios1–3.

### 4.1 API y tipos cerrados propuestos para G2

| Nombre propuesto | Entrada | Salida y límites |
|---|---|---|
| `read_handle_geometry(observed: _ObservedHandle) -> GeometryObservation` | Tipo exacto local, abierto, miembro de context.owned; parent real retenido | Dos respuestas NT completas y frozen; ninguna capacidad, scalar HANDLE ni partial-success |
| `derive_geometry_candidate(observation: GeometryObservation) -> GeometryDiagnostic` | Tipo exacto; estructuras frozen y bytes exactos validados | `candidate_b: int | None`, `causes: tuple[str, ...]`; función pura sin DLL/syscall/close |
| `_FileFsSectorSizeInformation` | Struct privada caller-owned | Siete c_uint32; tamaño28/alineación4 |
| `_FileAlignmentInformation` | Struct privada caller-owned | Un c_uint32; tamaño4/alineación4 |
| `NtSectorSizeObservation` | Frozen | `information_class=11`, `requested_bytes=28`, `ntstatus`, `iosb_status`, `information`, `raw: bytes` de28, siete campos unsigned32 |
| `NtAlignmentObservation` | Frozen | `information_class=17`, `requested_bytes=4`, `ntstatus`, `iosb_status`, `information`, `raw: bytes` de4, `alignment_mask: int` |
| `GeometryObservation` | Frozen | `source='nt-volume-sector11+nt-file-alignment17/v1'`, sector y alignment, cuatro MetadataObservation: parent/object antes/después |
| `GeometryDiagnostic` | Frozen | `source` igual, `candidate_b`, causas cerradas; sin accepted/trusted/writer/commit/admission flags |

Identificadores nuevos son inglés. No se añaden enums públicos o endpoints de producto.
Los siete campos copiados usan nombres `logical_bytes_per_sector`, `physical_bytes_per_sector_for_atomicity`, `physical_bytes_per_sector_for_performance`,
`filesystem_effective_physical_bytes_per_sector_for_atomicity`, `flags`, `sector_alignment_offset`, `partition_alignment_offset`.
Los campos de clase/status/info deben corresponder exactamente a sus raw. El derivador verifica bytes/tipos antes de usarlos.
Un objeto fabricado por el caller puede servir como fixture lógico; no prueba que el kernel lo observó ni concede capacidad.

El lector no acepta parent prestado como objeto geométrico, HANDLE int, propietario arbitrario o rutas.
No abre/reabre, duplica ni cierra el objeto; el caller mantiene su `_ObservedHandle` y lo cierra por el protocolo existente.
No carga DLL durante import portable. ABI/función ausente o plataforma distinta de Windowsx64 rechaza antes de iniciar una query.

### 4.2 ABI exacta y buffers

| Elemento | Representación Windowsx64 propuesta |
|---|---|
| HANDLE/PVOID | c_void_p,8bytes; nunca c_int/c_uint32 |
| NTSTATUS y enum de clase | c_int32,4bytes; no BOOL ni GetLastError |
| ULONG / Length | c_uint32,4bytes; no c_ulong dependiente del host |
| IO_STATUS_BLOCK | Reutilizar `_IoStatusBlock`: union Status:i32/Pointer:ptr en0, Information:c_size_t en8; size16/alignment8 |
| NtQueryVolumeInformationFile | WinDLL ntdll: argtypes=[c_void_p, POINTER(_IoStatusBlock), c_void_p, c_uint32, c_int32]; restype=c_int32; clase11, Length28 |
| NtQueryInformationFile | Misma firma ABI de cinco argumentos; clase17, Length4 |

`FILE_FS_SECTOR_SIZE_INFORMATION`: offsets0/4/8/12/16/20/24 para los campos en el orden de la tabla siguiente.
`FILE_ALIGNMENT_INFORMATION.AlignmentRequirement`: offset0. No `_pack_` improvisado ni parsing nativo del wire U1.
El binding verifica sizes, alignment y offsets antes de calls. Si difieren, no intenta una variante ABI.

| Offset | Campo NT de sectores |
|---:|---|
|0|LogicalBytesPerSector|
|4|PhysicalBytesPerSectorForAtomicity|
|8|PhysicalBytesPerSectorForPerformance|
|12|FileSystemEffectivePhysicalBytesPerSectorForAtomicity|
|16|Flags|
|20|ByteOffsetForSectorAlignment|
|24|ByteOffsetForPartitionAlignment|

Una arena compuesta conserva owner, ambos subarenas, dos IOSB distintos y buffers independientes de28 y4bytes.
No reutilizar memoria de la consulta anterior. El buffer y su backing estable están ligados por referencias fuertes antes de entrar al binding.
IOSB.Status comienza con sentinel distinto de0; Information con sentinel pointer-sized distinto de28/4; buffers contienen patrón inicial explícito.
No exigir que cada byte difiera del sentinel: un valor legítimo puede coincidir. Information exacto acredita la longitud reportada como escrita.
Status e Information sobrescritos, raw y campos derivados quedan registrados por separado; nunca se confunden zeros preinicializados con resultado.
No se exige B-alignment de estos buffers de metadata. El B-alignment de datos pertenece al writer futuro y necesita evidencia propia.

### 4.3 Orden, ownership e identidad

El lock global existente serializa toda la operación: precheck → parent-before → object-before → class11 → class17 → object-after → parent-after → copia frozen.
Cada metadata se obtiene mediante `read_handle_metadata` del componente aceptado. No se toma metadata de un receipt serializado.
El lector verifica wrapper abierto, pertenencia a context.owned, parent/context originales y misma adquisición antes y después de cada frontera.
Conserva referencias fuertes a observed→parent→owner. El caller-owner prestado coopera con el lock y mantiene físicamente el parent hasta completion o reap.
Una referencia Python no impide un CloseHandle externo: esa precondición independiente de U2b1 permanece obligatoria.

Las parejas before/after deben coincidir en volumen, ID128, path, kind, attributes, tag, links, delete-pending, EOF y allocation.
Cada lectura también debe pasar la política local U2b1. Cambios benignos del directorio pueden causar rechazo conservador; no se relaja para completar la query.
Parent y objeto deben compartir volumen. Volumen diferente, scalar revocado o wrapper cambiado rechaza; no sustituye el objeto ni mezcla adquisiciones.
No se exige que ID del parent y objeto sean iguales: son objetos diferentes. Paths/IDs observados no acreditan ownership S1 ni continuidad después del cierre.
Nunca se emite un resultado parcial de class11 si falla class17, la postmetadata, la comparación o el freeze.

### 4.4 Retorno, completion y fallos posretorno

Reglas propuestas de esta unidad; no cambian retrospectivamente la semántica de NtCreateFile aceptada en U2b1.

| Frontera | Regla exacta |
|---|---|
| Antes de entrar | Validación/ABI/binding/arena fallidos: cero calls; sin retención nativa ni close prestado |
| STATUS_PENDING0x103 | Retener arena compuesta completa y owner; poison global existente; cero lecturas de IOSB/buffer/metadata posterior y cero consultas adicionales |
| Sin retorno acreditado | BaseException durante llamada o transferencia posretorno: conservar arenas, estado y referencias; misma contención PENDING |
| Retorno noSUCCESS y noPENDING | Retorno signed32 gobierna; rechazar sin leer IOSB ni interpretar salida aunque contenga SUCCESS/info/raw plausibles; no fallback/retry |
| Retorno SUCCESS0 | Primero examinar IOSB.Status e Information efectivamente sobrescritos; sólo después copiar raw |
| IOSB.Status no0 o sentinel | Rechazar como completion inconsistente de geometría; no usar IOSB para sobreescribir un retorno de error |
| Information distinto de28/4 | Rechazar antes de leer/copiar payload; no short response, truncación, ampliar Length ni segunda consulta |
| Payload completo con valores desconocidos | Copia raw legítima disponible; el derivador devolverá candidate_b=None y causas |
| Rechazo completo conocido | NativeObservationError para transporte/coherencia de identidad; sin resultado parcial. Caller conserva handle para close ordinario una vez |
| Excepción posterior durante copias/construcción | Retención conservadora del composite antes de propagar IOCompletionUnaccreditedError, aunque retorno noPENDING ya observado |

Microsoft indica que el retorno noPENDING gobierna aun cuando IOSB.Status difiera. Exigir ambos0 es **política restrictiva propia de estas queries**.
No se afirma que igualdad sea requisito general de Windows. Un IOSB inesperado con retorno0 provoca rechazo conservador, no override del retorno ni espera.
Un NativeObservationError lanzado por un double dentro del binding sigue siendo ausencia de retorno; no lo tratar como rechazo completo sólo por su clase.
El parser/derivador puro puede rechazar después del retorno acreditado sin poison. Interrupción BaseException durante transferencia/freeze sí conserva custodia.
Los hooks after-return para futuros RED son privados: no callbacks públicos ni handler que libere una arena desde finally.

`context.call` y `context.retain` son la base aceptada. El scope de retención debe cubrir el composite antes de query1 y toda la transferencia hasta resultado frozen.
No basta retener raw copiado, scalar, IOSB temporal o sólo la segunda arena. La primera respuesta también permanece custodiada si query2 es incierta.
Tras poison, `close()` devuelve unknown sin syscall; nuevas operaciones del subsistema fallan antes del binding. Sin API de rehabilitación ni segunda arena unresolved.
No wait, poll, cancel, retry, CloseHandle para simular completion, async, timeout que libere buffers ni reap atribuido a completion individual.
La contención requiere retirada/reap del proceso propietario; esta API no mata procesos ni crea subprocess público automáticamente.
Los futuros doubles PENDING/posretorno sólo corren en hijo propio con padre que termina/espera/reapea; no se reclama PENDING nativo observado.
Interrupciones repetidas del propio handler siguen fuera de la garantía acreditada U2b1; no se declara tolerancia absoluta nueva.

### 4.5 Política de tamaños, flags, offsets y B

El lector preserva respuestas completas aunque su geometría no permita derivar B. El derivador no convierte ausencia en default4096.

| Dato | Validación para candidato B |
|---|---|
| Campos/bytes | int exacto no bool, unsigned32, raw bytes exactos28/4 y correspondencia LE; clases/status/info exactos |
| Cuatro tamaños | Cada uno potencia2 entre512 y65536; cada tamaño físico/efectivo≥logical y divisible por logical; cero es desconocido bloqueante |
| Relaciones entre tamaños | No exigir igualdad de físico atómico, rendimiento y efectivo; effective puede diferir. Todos deben cumplir el límite lógico anterior |
| AlignmentRequirement NT | Sólo{0,1,3,7,15,31,63,127,255,511}; alignment_bytes=mask+1 únicamente después de pertenencia.0 significa1byte, no unknown |
| Flags NT | Máscara conocida0xF. Bits0x1 aligned-device y0x2 partition-aligned deben estar ambos presentes para candidato |
| Bits0x4/0x8 | No-seek/TRIM, independientes. No se requieren y no alteran B. No inferir soporte de flush/write-through ni atomicidad a partir de ellos |
| Bits fuera de0xF | GEOMETRY_FLAGS_UNKNOWN; candidatoNone, raw conservado |
| Offsets0xffffffff | GEOMETRY_OFFSET_UNKNOWN, incluso si flags de alineación están presentes; no reemplazar por0 |
| Offsets conocidos | La primera política sólo acredita ambos exactamente0. Cualquier nozero bloquea candidato; no compensar el offset ni admitir por divisibilidad |
| Bit1 presente + sector offset nozero conocido | GEOMETRY_ALIGNMENT_CONTRADICTION además de offset no acreditado: el comienzo lógico no coincide con el físico |
| Bit2 presente + partition offset nozero | GEOMETRY_OFFSET_NOT_ACCREDITED; no afirmar contradicción universal, pues una posición absoluta nozero puede estar físicamente alineada |
| Bits1/2 ausentes + offsets0 | GEOMETRY_ALIGNMENT_NOT_CORROBORATED; no inferir los bits desde offsets ni tomar0 como capacidad |
| B candidato | max(cuatro tamaños,alignment_bytes); potencia2 dentro512..65536 y B divisible por cada tamaño y por alignment_bytes |

La política ambos offsets0 es restrictiva del proyecto, no una definición universal Microsoft de alineación.
No impone rango arbitrario a un offset nozero ni lo reduce módulo un tamaño para volverlo admisible. Es raw válido pero fuera del perfil acreditado.
Sustituir un tamaño0 por logical sería otra inferencia; sólo se acepta un fallback realizado por el filesystem y efectivamente reportado como valor válido.
La ausencia de bits4/8 no es contradicción. Flags3/7/11/15 pueden producir candidato si todo lo demás acredita alineación; Flags0/1/2/4/8/12 no.

`causes` contiene todos los incumplimientos detectables, únicos y en orden fijo: RAW_INVALID, GEOMETRY_SIZE_UNKNOWN, GEOMETRY_SIZE_INVALID,
GEOMETRY_SIZE_INCOHERENT, GEOMETRY_ALIGNMENT_MASK_INVALID, GEOMETRY_FLAGS_UNKNOWN, GEOMETRY_OFFSET_UNKNOWN,
GEOMETRY_ALIGNMENT_CONTRADICTION, GEOMETRY_OFFSET_NOT_ACCREDITED, GEOMETRY_ALIGNMENT_NOT_CORROBORATED, GEOMETRY_B_OUT_OF_WIRE.
No nace una nueva política de admisión basada en esas cadenas. Cualquier causa implica candidate_b=None.
La API impide división/modulo/cálculoB antes de validar los operandos. Los casos de límites imposibles tras las validaciones siguen comprobándose como invariantes.

**Control puro:** tamaños512/4096/4096/4096, flags3, offsets0/0, mask511 → candidate_b4096.
Mask0 con el mismo control sigue dando4096. Tamaños512/65536/4096/4096 →65536. Tamaños512/131072/4096/4096 →None.
Los controles son fixtures lógicos; no describen este host ni acreditan atomicidad sectorial.

### 4.6 Contradicciones, derivación y writer futuro

Query11 describe sectores; query17 describe alineación de buffers. No deben coincidir numéricamente: sector4096 y mask511 son coherentes.
No existe campo repetido para comparar entre ambas respuestas; su combinación válida exige límites, divisibilidad y la misma adquisición acreditada.
Un mask no permitido, clase equivocada o respuesta de otro handle bloquea el conjunto. Nunca sustituir un campo fallido por Win32, cache o respuesta histórica.
U2b2 no realiza consultas FileStorageInfo/FileAlignmentInfo Win32. Sus experimentos anteriores quedan separados, con sus propios status/flags.
Una discrepancia Win32/NT histórica no elige la autoridad: la decisión explícita selecciona NT para este perfil y conserva el límite documental Win32.

El writer posterior necesitará una adquisición nueva/exclusiva con derechos y modos propios, S1 completo y queries NT frescas en esa adquisición.
Debe acreditar B de buffers/datos/offsets y compatibilidad con la cabecera U1. Diferencia respecto al alignment de un journal existente bloquea; nunca recodificarlo para pasar.
Un candidato readonly anterior no autoriza abrir writer, crear journal, ampliar/truncar, flush, ACK o efectos. Tampoco prueba dureza de barreras/powerloss.

## 5. Impacto en módulos y ficheros

| Módulo / fichero (ruta real) | Cambio futuro o candidato | Nuevo / modificado |
|---|---|---|
| `scripts/storage_journal_windows.py` | Propuesta: structs28/4, firmas NT, lector con composite retenido y derivador puro; conservar U2a/U2b1 | Modificado sólo tras release futuro |
| `tests/test_storage_journal_windows.py` | Propuesta: RED causales por casos siguientes, regresión U2a/U2b1 y positivos NT ordinarios futuros | Modificado sólo tras release futuro |
| `scripts/storage_journal.py` | Referencia readonly de JournalLayout; no cambiar wire ni codec | Sin cambios |
| `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md` | Copia privada focal: sustituir autoridad Win32 en154 y referencias376/390/415; resto byteidéntico | Candidato `storage-durable-design.md` privado |
| `docs/decisiones/ADR-0078-geometria-nt-readonly-del-journal.md` | Candidato privado de autoridad y frontera B; ROOT verifica ID antes de publicar | Nuevo sólo tras decisión/revisión/adopción |
| `docs/decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md`, `ADR-0076-politica-estricta-de-confianza-del-journal-windows.md` | O2/S1 aceptadas; referencias de contexto | Sin cambios |

### Casos para el futuro RED, sin ejecutar tests aquí

Cada fila requiere fuente previa, control válido, mutation aislada, RED conductual antes del cuerpo y GREEN posterior.
Un missing-import, módulos ausentes o sentinel no adquirido no constituyen RED causal de este contrato.

| Caso | Mutation causal / control | Observación necesaria |
|---|---|---|
| R01 entrada/ABI | intHANDLE, borrowed como sujeto, cerrado, wrapper ajeno; tamaño/offsetABI wrong | Cero query, close o fallback; control wrapper local consulta por su handle |
| R02 firmas | Longitud28/4 y clases11/17 incorrectas | Double comprueba tipos/argumentos reales; retorno y raw independientes; Windows futuro verifica ambas firmas |
| R03 errorNT | ERROR/warning/informational con IOSB0/info exacto/raw válido | Ninguna lectura de salida ni consulta2 tras query1fallida; no interpretar NT_SUCCESS general |
| R04 IOSB | Retorno0 + sentinel/no0; control ambos0 escritos | Rechazo restrictivo sin override; pending IOSB con retorno0 tampoco se espera |
| R05 longitud | query1 Information0/27/29/max; query2 0/3/5/max | Rechazo anterior a lectura/copia; no clamp, reissue ni resultado parcial |
| R06 bytes | Buffer inicial patrón, double no escribe IOSB.Status o no reemplaza Information | Rechazo; control cambia payload y ambas salidas, no test de cero inicial |
| R07 PENDING query1 | IOSB/raw plausibles; instrumentar acceso prohibido | Arena/owner vivos tras error+GC, cero IOSB/raw/postmetadata/query2/close; siguiente contexto bloqueado |
| R08 PENDING query2 | Query1 completa; query2 devuelvePENDING | Retener composite con dos buffers y IOSB; no liberar query1 ni devolver partial-success |
| R09 posretorno | BaseException justo tras retornoPENDING; después SUCCESS; durante copias/freeze | Poison/retención causal antes de perder referencia; child propio reaped, sin reclamar completion nativa |
| R10 before-entry | Falla allocation/binding/argumentos antes syscall | Cero entered y ninguna retención nativa artificial; precondición de validación distingue R09 |
| R11 identidad | Cambiar ID/volumen/path/kind/tag/attrs/links/delete/eof/allocation antes/después, scalar/parentcontext cambiados | Cero GeometryObservation utilizable; no reabrir; parent y objeto comparados por parejas correctas |
| R12 tamaños | Cada campo0,511,513,131072; físico menor logical; effective múltiplo no válido | None+causas exactas; controles512/4096/65536 acreditados, physical/effective distintos admitidos |
| R13 máscara | 0,1,…511 controles;2/512/1023/0xffffffff/bool inválidos | mask+1 sólo tras pertenencia;0→1byte; sin aplicar máscara al campo Win32 |
| R14 flags | 3/7/11/15 controles;0/1/2/4/8/12, bit16/31 desconocido | No-seek/TRIM independientes; no candidate si falta acreditación1/2 o hay unknown |
| R15 offsets | UNKNOWN cadauno, nonzero cadauno con bits ausentes/presentes | Ambos0 requeridos; nozero ni múltiplo dephysical obtiene candidate; distinguir contradicciónsector y partitionnoacreditado |
| R16 combinación | Sector4096 + mask511 control; respuestas completas pero wrapper/campo/clase distinta | No exigir tamaños iguales a alignment; no mezclar adquisiciones/APIs |
| R17 salida pura | bool/bytearray/raw length wrong/fields contradict raw/source wrong y dataclass fabricada | Rechazo puro sin DLL; fixture válido sólo produce número lógico; nunca capacidad |
| R18 custodia close | Pending y close repetido; cierre ordinary tras rechazo completo | Cero syscalls tras poison; resultado closeunknown; ordinary una llamada máxima; prestado jamás close |
| R19 no ampliación | Escribir raw/candidate en receipt, invocar writer/admission/fallback desde geometría | Ninguna API de efectos disponible; wire/U1 exacto y regresiónU2a/U2b1 conservada |
| R20 nativo futuro | Archivo/directorio ordinario propios con dos queries reales y metadata mismaadquisición | status/info/raw auténticos; diagnósticoNone aceptable si host no acredita política; no forzar un positivo de admisión |
| R21 portable | Import Linux sin DLL y derivador con mismosbytes; lector rechaza plataforma | Prueba lógica portable separada de NT Windows, sin ctypes.last_error falso en fixture |

No existen resultados RED/GREEN de U2b2 en esta entrega. Cobertura whole nueva/cambiada≥80%, sin exclusiones, Ruff y revisiones A/B/C más Dauto
pertenecen a la unidad futura autorizada. La QA aceptada de U2b1 no sustituye estos gates.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Confundir IOSB con retorno | Media | Aceptar salida de error o leer pending | Tabla4.4; política ambos0 explícita, retorno gobierna; RED error/pending/completion |
| Perder arenas posretorno | Media | Uso de memoria liberada por kernel | Composite antes de entrar, retención global y RED query2/transferencia; reap owner |
| Interpretar flagsWin32 comoNT | Media | Geometría aceptada por inferencia | Sólo class11 con fuenteNT cerrada; ninguna queryWin32 en unidad |
| Rechazar una geometría legítima nozerooffset | Deliberada | Host no genera candidato | Raw preservado, causas; otra política exige ADR y evidencia, no bypass |
| Mismo-SID hostil o administrador | Fuera de garantía | Cerrar/cambiar adquisición o código | Conservar supuesto deployer/owner confiable de ADR0075/76; sin nueva protección inventada |
| Metadata cambia aunque queries completas | Posible | Snapshot incoherente | Comparar antes/después y bloquear, sin reintento automático |
| CandidatoB usado como token | Media | Efectos sin S1/modos/buffers | Dataclasses sin handles/capacidad; writer reconsulta su propia adquisición |
| Copy source/licencia de referencia | Evitable | Ingreso de código ajeno sin trazabilidad | HTML/header sólo lectura documental; ninguna SDK/dependencia/herramienta nueva; stdlib existente |
| Biblioteca/runtime añade dependencia | No propuesta | Contradecir registro legal | Mantener ctypes/stdlib y DLLSO existentes; cualquier nueva herramienta requiere fila legal antes de ingreso |
| Presupuestos previos insuficientes | No recalculada | Gate nativo pendiente | ROOT libera alcance y conserva requisitos; evaluator/planner reevaluarán si corresponde, sin horas inventadas |

El registro legal acredita Python existente, no una redistribución del SDK, código de Terminal o Windows.
La entrega no afirma una auditoría de licencias ni derechos de redistribución de páginas HTML. Las referencias no se convierten en dependencia de producto.

## 7. Preguntas abiertas

1. G2 fue elegida explícitamente por ROOT y queda registrada arriba. Revisión fresca, QA documental y adopción canónica completadas; implementación pendiente de release y evidencia conductual.
2. ROOT verificó libre ADR-0078 antes de publicar este contrato. ADR-0077 de M2 permanece intacto.
3. Prueba nativa de ambas funciones, exportntdll, ABI exacta y comportamiento del host pendiente. Si falta evidencia, gate cerrado.
4. G2 confianza de cadena, bootstrapTI, adquisiciónwriter/S1, store/ACK/crash/lifecycle y ext4 persistente siguen pendientes de otras unidades.
5. U2b1 no acredita resistencia a interrupciones repetidas del handler de retención; este contrato no amplía esa garantía.

No hay incógnita pendiente de forma/firma/políticaB en la recomendaciónG2. Las filas anteriores distinguen decisiones documentales completadas de evidencia nativa y durabilidad aún pendientes.

---

## Changelog

| Fecha | Cambio |
|---|---|
|2026-10-11|Primera entrega borrador preservada exacta en attempt1; ROOT eligióG2. Aprobación sólo privada, sin release/canon; enlaces preparados para overlay canónico|

|2026-10-11|ROOT adopta G2 y ADR0078 tras revisión A+B1 y QA documental33/33 intento3. Minor A01 anotado; sin ejecución nativa ni aceptación M1. Recibo 2026-10-11T12:16:41.617978+00:00|
