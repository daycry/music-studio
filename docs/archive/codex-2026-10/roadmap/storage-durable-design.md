---
design: storage-durable-lifecycle
titulo: Recibo durable y ciclo de vida del VHDX propio
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: spec.md
evaluacion: n/a
plan: improvement-plan.md
adr: ../../decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md
storage_nt_security_policy: storage-nt-security-policy.md
opcion_elegida: O2
validada_por: ROOT bajo delegación vigente del propietario
validada_fecha: 2026-10-11
revision_documental: A/B conforme, intento 2
generacion:
  fuente: estimado
  medidor: root:m1/lote-execve-harness-storage-design
  tokens: null
  coste: null
---

# Diseño — Recibo durable y ciclo de vida del VHDX propio

> ROOT eligió O2 bajo la delegación vigente del propietario. La revisión documental A/B del intento 2 está conforme. La implementación y la QA física siguen pendientes.

| Campo | Valor |
|---|---|
| Estado | Diseño aprobado; revisión documental A/B conforme, implementación y QA pendientes |
| Opción elegida | O2: journal estable con generaciones inmutables y sellos dentro del mismo archivo |
| Validación | ROOT, 2026-10-11, por delegación vigente del propietario; sin consulta nueva |
| ADR | [ADR-0075](../../decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md), aceptada bajo delegación |
| Alcance de evidencia | Lectura de fuentes actuales y documentación primaria. No se ejecutaron probes, provisión, attach, GPU ni comandos elevados |

## 1. Contexto y restricciones

ADR-0069 exige ext4 dentro de `data/_storage/studio-data.vhdx`. ADR-0071 conserva el helper Docker y sus dominios aislados. La Constitución §2 reserva SQLite de producto al server. Este controlador registra infraestructura en archivos dentro del proyecto; no abre ni escribe SQLite.

La preparación elegida sigue siendo ext4 offline, conversión a VHDX y publicación NOREPLACE. No se reabre esa decisión. El producto sigue en Docker; Ollama conserva su excepción WSL2. Este trabajo no usa VRAM ni modifica su arbitraje.

| Fuente actual | Hecho que condiciona el diseño |
|---|---|
| `scripts/storage_receipt_store.py` | `ReceiptLease` abre sólo recibos existentes, compara bytes del mismo handle, retiene ancestros y niega WRITE/DELETE. No crea ni guarda |
| `scripts/storage_operator.py` | `PublishedDiskBinding.open` exige exactamente un `StorageReceipt` en `published`. Consulta identidad nativa; no concede `OwnedFile` ni write |
| `scripts/storage_attach.py` | Retiene binding durante los comandos, pero lee por ruta y termina con `plan.receipt_path.write_bytes(advanced.to_bytes())` |
| `scripts/storage_offline.py` | El executor devuelve `vhdx_verified` y escribe JSON por ruta; no es el nuevo controller durable |
| `scripts/storage_publish.py` | Promueve NOREPLACE y luego escribe el recibo. Falta intención durable previa y reconciliación de la ventana rename/recibo |
| `packages/storage-guard/studio_storage_guard/receipt.py` | Recibo v1 y fases estrictas `reserved→raw_verified→vhdx_verified→published→attached→validated` |
| `packages/storage-guard/studio_storage_guard/provision.py` | `provision_domains` sólo opera sobre una raíz nueva/vacía. Repetirlo en una biblioteca usada no es recovery |
| `scripts/storage.py`, `.ps1`, `.sh` | Política PLAN-ONLY. No se libera accidentalmente al añadir un módulo nuevo |

Los componentes aceptados `ReceiptLease` y `PublishedDiskBinding` conservan sus fuentes y tests. El journal se implementa en módulos nuevos. El controlador conserva un snapshot v1 histórico de `published` para adquirir el binding existente.

El VHDX publicado actual es SMOKE de 64 MiB. No acredita disco de producción de 64 GiB. Una reserva de producción encuentra ese destino y devuelve `CONFLICT` sin escribir, mover ni adoptar. No se usa un UUID de fixture como evidencia real.

**Frontera de confianza.** El deployer del host y el principal Windows autorizado son confiables, como el controller de plataforma de ADR-0071. El diseño resiste objetos ajenos, carreras, alias, procesos rivales y crashes dentro de esa frontera. No promete resistir a un administrador ni a código malicioso con el mismo SID capaz de cambiar DACL y falsificar todo el historial después del cierre.

## 2. Opciones (3)

### O1 — Reemplazar un JSON v1 mutable bajo lock

Crear un temporal exclusivo, escribirlo y sustituir el JSON actual. Un lock separado serializa escritores cooperativos. La API permanece próxima al recibo actual.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: lock y rotación de identidades/handles |
| Riesgo | Alto: soltar protección DELETE introduce una ventana; los lectores existentes niegan replacement; falta garantía documentada equivalente a fsync del directorio |
| Coste relativo | S |
| Reversibilidad | Alta en formato, baja si se sobrescribió el único historial |

`ReplaceFileW` opera con nombres y abre accesos DELETE. Su opción `REPLACEFILE_WRITE_THROUGH` no está soportada. Sus errores pueden dejar nombres distintos y el file ID final procede del replacement. No ofrece CAS contra el contenido anterior. [Microsoft: ReplaceFileW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew).

No se recomienda. `write_bytes + fsync + reread` tampoco proporciona exclusión, autoridad por handle ni atomicidad entre efectos y recibo.

### O2 — Journal estable de generaciones inmutables y sellos por handle

Crear una vez un journal de infraestructura. Reservar su capacidad antes de admitir efectos. Cada cambio escribe un slot nuevo con el snapshot completo, intención/resultado, predecesor y sello. El nombre, file ID y EOF permanecen estables durante las transiciones.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: codec acotado, exclusión nativa, dos barreras y recovery explícito |
| Riesgo | Medio: fallo/torn-write detiene admisión; bootstrap y hardware conservan límites explícitos |
| Coste relativo | M |
| Reversibilidad | Alta: JSON histórico y todas las generaciones se conservan; rollback de writer mantiene startup bloqueado |

Un único handle exclusivo serializa CAS. Las generaciones anteriores no se reescriben. El JSON v1 es semilla y representación histórica, nunca el puntero mutable de autoridad. No aparece otra BD ni otro servicio.

**Recomendada.** Evita un rename de namespace en cada commit y permite distinguir intención durable, efecto observado, resultado sellado y respuesta perdida.

### O3 — JSON por generación más archivos COMMIT exclusivos

Crear `generation-N.json` inmutable y después `commit-N` NOREPLACE, ambos bajo exclusión nativa. El lector busca una cadena de markers íntegra. El JSON inicial se conserva.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: codec JSON conocido y directorio de generaciones |
| Riesgo | Medio-alto: cada transición vuelve a depender de persistencia de nombres; markers parciales y archivos huérfanos requieren reconciliación |
| Coste relativo | M |
| Reversibilidad | Alta: conserva generaciones; la limpieza segura del directorio agrega una frontera |

`FILE_RENAME_INFO` con `ReplaceIfExists=FALSE` rechaza un destino existente y permite root relativo por handle. Documenta NOREPLACE, pero no un contrato general de persistencia del directorio tras corte eléctrico. [Microsoft: FILE_RENAME_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info).

Esta opción es viable para publicación de artefactos, pero menos adecuada como autoridad mutable de todas las fases. No se identifica el último commit por mtime ni por el nombre lexicográficamente mayor.

## 3. Criterios de decisión

1. Preservar datos, evidencia previa y exclusión real antes de simplificar el formato.
2. Mantener identidad por handle, file ID, volumen, cadena de padres y política de seguridad antes y después de cada efecto.
3. Distinguir commit, ACK y cierre. Un timeout o excepción no equivale a ausencia del efecto.
4. Recuperar desde intención y observación actual. Nombre, SHA, PID, device de otra sesión y fase histórica son insuficientes.
5. Probar ahora CAS/custodia/recovery de archivos con CPU Windows sin administrador. Reservar montaje y persistencia ext4 para evidencia nativa elevada posterior.
6. Mantener los contratos v1, el server como writer de producto y las restricciones de ADR-0069/0071.

## 4. Recomendación · opción elegida y por qué

**Recomendación del arquitecto: O2.** El archivo estable reduce cambios de namespace y permite CAS por identidad y generación sin sustituir lectores aceptados. O1 se descarta por replacement y exclusión incompatible. O3 se descarta por repetir el riesgo de nombres en cada transición.

**Opción elegida: O2 por ROOT el 2026-10-11.** ROOT ejerció la delegación vigente del propietario de tomar las mejores decisiones. La revisión documental A/B del intento 2 quedó conforme. La elección no declara aceptación técnica ni cierre de T-05.

### 4.1 Fuente de verdad y formato

El journal físico propuesto es `data/_storage/storage-control.journal`. No contiene canciones, jobs, takes ni copias de SQLite. Registra exclusivamente reserva, identidad de archivos propios, fases y sesiones del almacenamiento.

El codec es `journal_version=1`, separado de `StorageReceipt.schema_version=1`. No cambia la clase de recibo aceptada ni su transición terminal. Cada snapshot devuelve bytes exactos e inmutables; los diccionarios parseados no son la autoridad CAS.

| Campo de generación | Contrato |
|---|---|
| `generation`, `slot_index`, `previous_commit_sha256` | Cadena estricta; sin forks ni selección por fecha |
| `journal_id` | UUID aleatorio nuevo en creación; constante en toda la cadena y distinto del UUID ext4 |
| `operation_id`, `request_id`, `request_sha256` | Operación de provisión y solicitud idempotente separadas; IDs reales, no fixtures |
| `receipt_payload`, `receipt_sha256` | JSON canónico v1 completo y hash de esos bytes |
| `published_receipt_payload` | Snapshot exacto histórico en `published`, guardado cuando se alcanzó esa fase; sólo para `PublishedDiskBinding.open` |
| `journal_identity`, `project_identity`, `parent_chain` | Volumen+file ID de objetos retenidos y paths canónicos; tipo, reparse, links y política se revalidan |
| `owned_objects` | Papel, identidad nativa, padre acreditado, nombre permitido y origen de creación/reserva; SHA no sustituye autoridad |
| `intent` | Acción pendiente, request, estado previo, evidencia y objetos exactos autorizados; sin comandos arbitrarios del JSON |
| `session` | Epoch propia, distro, raíz canónica, observaciones actuales, estado operativo y estado de admisión |
| `result` | Resultado observado o `unknown`, causa primaria, fallos de flush/cleanup/close y límites de la observación |

El formato rechaza claves duplicadas, números booleanos, enums abiertos, exceso de longitud, path no canónico, historia incompleta y versiones desconocidas. Tamaño máximo del payload: 1 MiB. Hashes incluyen tipo de frame, versión, índice, longitud y payload; no sólo el contenido JSON.

`operation_id` conserva su formato ULID de 26 caracteres. Cada `request_id` es ULID nuevo del controller. `journal_id` usa UUID aleatorio canónico generado al crear; el UUID ext4 se genera sólo para raw nuevo y se acredita después con las herramientas fijadas. Recovery conserva los IDs observados, nunca los sustituye. No existen GUID, UUID ni tokens secretos de ejemplo utilizables como autoridad en este documento.

| Respecto al JSON v1 | Compatibilidad concreta |
|---|---|
| `schema_version`, `operation_id`, `phase`, `disk_path`, `size_bytes`, `history` | Se conservan dentro de `receipt_payload`; mismos campos, tipos y orden de fases. El seed histórico no se modifica |
| Sobre `receipt_payload` | Envelope nuevo `journal_version`, generación, cadena, request, capacidad/identidades y sesión. No se añaden claves al schema v1 |
| Sobre archivo físico | Journal binario alineado con cabecera y slots; `StorageReceipt.from_bytes` no puede consumirlo directamente |
| Lectores nuevos | Codec journal → snapshot sellado → parseo v1 del payload; rechazan journal desconocido y ausencia de autoridad |
| Lectores v1 existentes | Siguen leyendo el seed o un export histórico declarado; sus bytes no representan el head operativo |
| Resultado de API | `JournalSnapshot` y `JournalToken` nuevos; attach puede conservar la proyección `StorageReceipt` para diagnóstico, sin convertirla en autoridad de writer |

**Layout propuesto:** cabecera inmutable alineada y 64 slots de capacidad fija. Cada slot tiene PREPARE+payload padded y un bloque COMMIT aparte. Cabecera y slots quedan inicializados con escrituras reales y flush antes del primer efecto. No sparse, compresión, streams alternativos ni truncación para reutilizar slots. La capacidad ocupa aproximadamente 64 MiB; su longitud exacta depende de la alineación acreditada. Agotamiento devuelve `JOURNAL_FULL` antes de efectos. Rollover/compactación queda fuera de la primera implementación, con preservación total y gate cerrado.

La autoridad geométrica G2 aceptada por ROOT usa `NtQueryVolumeInformationFile(FileFsSectorSizeInformation=11)` y `NtQueryInformationFile(FileAlignmentInformation=17)` sobre la misma adquisición propia retenida; su contrato está en [ADR-0078](../../decisiones/ADR-0078-geometria-nt-readonly-del-journal.md), aceptada tras revisión A+B1 y QA documental33/33; implementación nativa pendiente. U2b2 devuelve observaciones readonly separadas y deriva sólo B candidato: cuatro tamaños NT acreditados, máscara NT validada antes de mask+1, flags NT1/2 corroborados y ambos offsets conocidos cero; unknowns, bits desconocidos o incoherencias bloquean el candidato. No mezcla FileStorageInfo Win32 ni usa fallback. El writer posterior reconsulta su propia adquisición y acredita modo, capacidades, datos, offset y buffers alineados; el candidato readonly no admite escritura ni ACK. No se presume atomicidad de 4 KiB ni de un sector. [Microsoft: query de volumen NT](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryvolumeinformationfile), [query de alineación NT](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryinformationfile), [File buffering](https://learn.microsoft.com/en-us/windows/win32/fileio/file-buffering).

### 4.2 Capacidades nativas y CAS

El módulo nuevo abre cada componente desde el handle del padre, con nombre de un componente, `FILE_OPEN_REPARSE_POINT` y tipo cerrado. Crear usa `NtCreateFile(FILE_CREATE)` y exige `IO_STATUS_BLOCK.Information=FILE_CREATED`; abrir usa `FILE_OPEN`. Nunca `OPEN_IF`, overwrite ni crear tras encontrar un objeto ajeno. `RootDirectory` permite apertura relativa; write-through y no-buffering son opciones distintas. [Microsoft: NtCreateFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile).

El writer solicita READ/WRITE reales y comparte **cero** en el journal. Los ancestros retienen TRAVERSE/READ_ATTRIBUTES y niegan DELETE; no basta un handle con acceso cero. Otros writers o lectores activos impiden adquirir writer. El lector del journal retiene READ y sólo SHARE_READ, y se libera antes de intentar writer. No hay upgrade de la lease v1 ni handoff con ventana. Sharing se comprueba en ambos sentidos; un fallo deja cero efectos. [Microsoft: CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

Además de sharing, se comprueban owner y DACL por handle; sólo el principal autorizado, SYSTEM y administradores tienen write/delete/WRITE_DAC. No se cambian ACL de padres existentes para obtener acceso. La cadena del proyecto conserva sus identidades. Un dominio que permite alterar los nombres a un principal fuera de la frontera confiable no se adopta. [Microsoft: GetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo).

**G2 — política S1 elegida por ROOT:** [admisión estricta de dominio y cadena](storage-nt-security-policy.md), con excepción exacta de owner TrustedInstaller sólo en el root del volumen del sistema ([ADR-0076](../../decisiones/ADR-0076-politica-estricta-de-confianza-del-journal-windows.md)). Desconocidos y grants efectivos outsider peligrosos mantienen SECURITY_UNACCREDITED sin modificar ACL existentes. S2 sólo aporta evidencia experimental de lease; S3 queda aplazada. Esta definición no cambia el wire U1 ni acredita G2 nativo o producción.

`JournalToken` contiene identidad del journal, identidad de raíz/padres, última generación y digest del commit. Ningún API acepta `expected_sha` suelto o sólo `expected_path`. El writer adquirido relee la cadena desde su handle y compara el token completo. El mismo proceso usa RLock para lectura/seek/write/revalidate; no mantiene este lock durante código externo arbitrario.

El commit sigue esta secuencia bajo writer exclusivo:

1. Revalidar journal, padres y capacidades de artefactos. Comparar token, request y transición válida.
2. Elegir el siguiente slot nunca usado. PREPARE y cuerpo completo se escriben sólo por ese handle.
3. Comprobar número exacto de bytes y `FlushFileBuffers` del journal. Revalidar identidad y releer el frame por handle.
4. Escribir COMMIT con identidad/generación/predecesor/digest del PREPARE. Flush y revalidación nuevamente.
5. Devolver token nuevo y ACK sólo tras comprobar el sello completo. Un fallo después de iniciar escritura devuelve `COMMIT_UNKNOWN`, no éxito ni rollback del archivo.

Se solicita write-through y no-buffering con buffers alineados propios. `FlushFileBuffers` necesita acceso de escritura y fuerza buffers del archivo. El flush de todo el volumen requiere privilegios y no se utiliza. [Microsoft: FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers).

Una solicitud repetida con el mismo `request_id` y los mismos bytes devuelve el commit ya sellado; no escribe otra generación ni ejecuta otra vez el efecto. Mismo ID con payload diferente devuelve `REQUEST_CONFLICT`. CAS viejo sin esa solicitud sellada devuelve `STALE_GENERATION`.

**Invariantes que verifican los tests del store:**

| ID | Invariante observable |
|---|---|
| J01 | Un writer tiene exclusión READ/WRITE/DELETE efectiva del journal. Writer rival y read view nueva no se adquieren mientras vive |
| J02 | Una read view retiene READ, niega WRITE/DELETE y devuelve sólo cadena completa de slots sellados. El writer no adquiere mientras vive esa view |
| J03 | El head leído no autoriza un efecto. El writer relee y CAS-compara identidad, padres, generación, digest y request después de adquirir exclusión |
| J04 | Cabecera, EOF reservado y slots ya usados son inmutables. Una escritura nueva tiene offset dentro de un slot completamente nuevo y fuera de slots previos |
| J05 | Ningún efecto externo empieza hasta ACK de su intención sellada. Ningún resultado exitoso sale antes de ACK de su completion sellada |
| J06 | READ/WRITE/SEEK/flush del store siempre usan el handle retenido, nunca reopen por nombre. Metadata/ACL/padres y capacidades del efecto se revalidan antes y después de cada frontera |
| J07 | Bytes escritos deben igualar bytes solicitados. PREPARE y COMMIT nunca comparten bloque con una generación anterior ni entre sí |
| J08 | Los sellos se aceptan sólo con longitud, formato, identidad, request, predecesor y digest completos. Un hash válido aislado no concede write ni dominio propio |
| J09 | Después de escritura/flush/close inciertos, el objeto local pierde autoridad antes de exponer el fallo. Ningún `finally` repite write, rename, mount o scalar CloseHandle |
| J10 | Idempotencia busca el request en toda la cadena sellada válida. Una respuesta perdida no consume otro slot ni dispara otro efecto; un intent pendiente exige reconcile |

**Cutpoints de commit:**

| Corte | Momento | Resultado y recuperación |
|---|---|---|
| C0 | Antes de PREPARE | Rechaza sin escritura. |
| C1 | Durante PREPARE/body | Conserva el slot. Devuelve incertidumbre si hubo escritura. |
| C2 | Tras write, antes de flush1 | Conserva el slot. Devuelve incertidumbre si hubo escritura. |
| C3 | Tras flush1 y relectura | Conserva el slot. Devuelve incertidumbre si hubo escritura. |
| C4 | Durante COMMIT | Conserva el slot. Devuelve incertidumbre si hubo escritura. |
| C5 | Tras write, antes de flush2 | Conserva el slot. Devuelve incertidumbre si hubo escritura. |
| C6 | Tras flush2, antes de ACK | Recupera el mismo commit/request tras abrir, validar y hacer flush nuevamente. |
| C7 | Durante cleanup/close | Conserva el commit sellado con cleanup incierto. Nunca repite el efecto. |

No se denomina `fsync` POSIX a ninguna de estas barreras. La implementación Windows llama directamente a `FlushFileBuffers` y comprueba su resultado. No llama a `os.fsync`, `write_bytes` o close como sustitución de la secuencia. En ext4, los flush de provisión/consumidores pertenecen al contrato Linux separado.

`CommitOutcome` separa `commit_state={sealed,rejected,unknown}` y `cleanup_state={closed,unknown}`. `sealed/unknown` significa commit acreditado y cierre incierto; no permite ACK de efecto repetido ni reutilizar la lease. El diagnóstico incluye request, token observado y causas, sin números de handle reutilizables. Un adapter CLI devuelve error ante cleanup incierto, preservando que el commit pudo quedar sellado.

### 4.3 Create, apertura autorizada y compatibilidad v1

| API pequeña propuesta | Efecto y precondiciones |
|---|---|
| `JournalStore.create_new(project, operation_id, size_bytes)` | Reserva dominio/journal nuevos con capacidades de creación; final existente bloquea; primero sella `reserved` |
| `JournalStore.bootstrap_published(project, seed_path, expected_seed, expected_binding)` | Importación explícita de infraestructura publicada previamente acreditada, no adopción automática por ruta/hash |
| `JournalStore.open_existing(project, journal_path)` | Adquiere handles y revalida identidad propia, política, formato y cadena; ausencia no crea ni busca otro journal |
| `store.read_snapshot()` | Devuelve envelope inmutable y token; lectura sola no concede write ni capacidad de disco |
| `store.commit(expected_token, request, transition)` | CAS durable interno descrito arriba; no ejecuta herramientas ni comandos |
| `controller.record_verified(expected, phase, owned_evidence)` | Avanza sólo una fase y exige capacidad viva y resultados reales; no acepta evidencia dict arbitraria del CLI |
| `controller.publish(expected, request_id)` | Intención durable con ID del incoming antes de NOREPLACE; completion con mismo ID final después |
| `controller.attach(expected, request_id)` | Intención de nueva epoch, binding publicado histórico y admin real; completion sólo tras observación actual |
| `controller.validate(expected, request_id)` | Provisión nueva o auditoría existente diferenciadas; probes reales y cierre/cleanup comprobados antes de completion |
| `controller.detach(expected, request_id)` | Cierra admisión, quiesce/flush propios y detach exacto; conserva todo el disco y el historial |
| `controller.reconcile(expected, request_id)` | Reacredita capacidades; resuelve sólo la intención exacta pendiente, nunca escoge disco por enumeración/posición |

Bootstrap v1 adquiere `ReceiptLease` del JSON y `PublishedDiskBinding` del disco. ROOT aporta el snapshot e identidad revisados, aún vigentes al adquirir ambas leases. Se validan root/ancestros/ACL, volumen+file ID y tamaño declarado antes de crear el journal. Un seed sin historial publicado o sólo SHA/path devuelve `LEGACY_UNACCREDITED`.

El journal bootstrap conserva la identidad nativa y los bytes íntegros del seed. Durante bootstrap, las leases se retienen hasta sellar la generación inicial. Después el seed no se actualiza nunca. Legacy `attached` no se toma como autorización de sesión. El SMOKE actual sólo admite registro explícito como SMOKE si ROOT lo libera; este documento no concede esa autorización ni ejecuta bootstrap.

El controller nuevo exige journal. Si sólo existe JSON v1, devuelve diagnóstico readonly/PLAN-ONLY. No cae al antiguo execute writable. `StorageReceipt` y sus lectores aceptados se conservan. Para una operación futura, se extrae el snapshot histórico `published` del journal y se entrega al binding existente. No se fuerza que el binding acepte `attached`/`validated` ni se fabrica autoridad reconstruyendo desde un JSON viejo.

Los antiguos CLI ejecutables de offline/publish/attach requieren wiring explícito para delegar al controller. Sus modos plan y parseo se mantienen. Después del corte, todos los caminos con efectos rechazan ausencia de journal; no quedan dos writers. Los wrappers actuales siguen bloqueados hasta ese corte y su QA.

### 4.4 Fases históricas y sesiones actuales

El recibo v1 conserva sus seis fases y sólo las alcanza una vez. Después de `validated`, reattach/detach no hace retroceder fases ni inventa fases v1. Las operaciones repetidas usan generaciones de sesión en el envelope.

| Estado operativo | Evidencia y gate |
|---|---|
| `inactive` / `detached` | Sin admisión; final propio conservado |
| `attach_intent` | Se ha sellado intención para epoch nueva. No acredita montaje |
| `attached` | Resultado actual de VHDX/device/UUID/mount bajo binding y gate cerrado |
| `validate_intent` | Montaje actual retenido; todavía sin admisión de producto |
| `validated` | Dominios auditados, helper y probes reales de cada rol; permite configurar despliegue propio, conservando preflight fresco |
| `quiesce_intent` / `detach_intent` | Admisión cerrada durablemente; operaciones nuevas bloqueadas |
| `unknown` | Identidad, efectos, commit o cleanup inciertos; gate cerrado y datos preservados |

Un nuevo proceso o reinicio no reutiliza una lease. Reconcile observa el montaje actual y crea observación de sesión nueva antes de reabrir admisión. `validated` en disco es evidencia histórica, no capacidad transferible. Los preflights por FD de ADR-0071 siguen siendo obligatorios en cada consumidor.

**Validated.** La primera vez llama `provision_domains` sólo si se acredita raíz propia nueva/vacía. Después arranca helper Docker propio y prueba los roles reales library-server RW, engine-library RO y engine-raw RW. Usa protocolo fresco challenge/FD y cleanup de ADR-0071. Registra UUID, root, resultado NOREPLACE y política/roles sin transportar PIDs/FDs como autoridad futura. El v1 pasa a `validated` sólo después de estos resultados.

Después de crash parcial de provisión, no se llama ciegamente otra vez a `provision_domains`. Un auditor readonly nuevo verifica dominio completo o clasifica `PROVISION_INCOMPLETE`. Completar un dominio parcial exige un contrato separado que acredite entradas creadas propias. Si no existe esa evidencia, se conserva el disco y se bloquea; no chown-R ni borrar/reformatear.

**Detach.** Todos los start/stop propios soportados atraviesan el gate del deployer, serializado por el mismo journal writer. Se sella cierre de admisión y se quiescen sólo los consumidores propios por IDs reales previamente acreditados. Server termina sus workers y flush/backup lógico; el host no escribe su BD. Se acredita parada de server, engines y helper y ausencia de consumidores ajenos. Un consumidor desconocido o namespace no auditable devuelve `BUSY_OR_UNKNOWN`.

Sólo después se fuerza el flush de la raíz ext4 por FD retenido, se desmonta el mountpoint exacto sin lazy/force y se ejecuta `wsl --unmount <VHDX exacto>` bajo binding revalidado. La documentación WSL exige privilegios para montar y advierte que omitir el disco en unmount desmonta todos. Nunca se omite ese argumento. [Microsoft: montaje WSL](https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk).

La ausencia de ese montaje/dispositivo se observa nuevamente antes de `detached`. Un error o cierre incierto conserva `unknown`; no copia el VHDX activo como backup. No se detiene WSL, Docker u Ollama globalmente. Detach no se libera para ejecución hasta disponer de admisión serializada y prueba real de todas sus namespaces consumidoras.

### 4.5 Recovery y compensación

| Corte/fallo | Acción segura tras reacreditar autoridad |
|---|---|
| Crash durante creación inicial del journal | Sin generación inicial válida no se admite ningún efecto. Conservar archivos; no recrear encima ni adoptar final |
| PREPARE incompleto o COMMIT ausente | No tratar la generación como committed. Conservar slot; cerrar admisión. Resolver desde última intención sellada y realidad |
| COMMIT íntegro, crash tras flush antes de ACK | Reabrir/revalidar, comprobar cadena y misma request; flush del handle antes de ACK recuperado; devolver token ya existente |
| Error/interrupt durante flush o después del sello | `COMMIT_UNKNOWN`; no repetir efectos. Reconcile decide si existe el mismo commit íntegro |
| Corrupción interior, fork o sello inválido | `JOURNAL_CORRUPT`; no seleccionar prefijo viejo para operar, no truncar ni aceptar una generación posterior automáticamente |
| Raw/VHDX creado, sin evidencia suficiente | Conservar; no hash-adoptar, reformatear ni borrar. Reconcile sólo retoma un objeto con reserva+identidad nativa durable |
| Publish intent sellado, crash antes de rename | Incoming propio con misma identidad puede completar NOREPLACE; destino ajeno produce CONFLICT y se conserva |
| Rename terminado, completion ausente | Comparar final contra identidad del incoming registrado antes del rename y padres/ACL; sólo entonces completion `published` |
| Attach intent sin completion | Inspección actual bajo binding; UUID único y mount exacto pueden acreditar completion. Si asociación ambigüa, conservar y bloquear |
| Crash tras attached o validated | Nueva epoch y auditoría actual. No repetir provisión vacía ni acreditar montaje con el receipt viejo |
| Quiesce/detach parcial | Admisión cerrada; observar primero. Reanudar sólo desmontaje propio aún presente o registrar detached ya observado |
| CloseHandle fallo/interrupción | Retirar scalar de autoridad antes de llamar, no retry del valor; conservar causas y `CLOSE_UNKNOWN`; proceso propietario debe finalizar antes de recovery por otro writer |
| Runtime revoca identidad | Cero comandos adicionales por ruta, incluyendo rollback. Conservar y registrar unknown si el journal todavía tiene autoridad |

No se destruye un final publicado para compensar un fallo de attach o del recibo. Compensación de montaje sólo se admite con binding, misma epoch, dispositivo/UUID/mount actuales y unmount exacto. Si no puede acreditarse, se preserva y se informa.

Un slot no sellado nunca se reutiliza. Un recovery puede reservar otro slot y sellar una resolución explícita del intento, incluyendo el slot incierto observado. No se salta corrupción de una generación sellada ni se usa un sucesor detrás de un hueco sin esa resolución verificable. Si no puede distinguirse una cola incompleta de daño histórico, se bloquea.

Un archivo truncado, EOF distinto de la capacidad fijada, cabecera incompleta o identidad cambiada devuelve `JOURNAL_CORRUPT_OR_UNKNOWN`. No se extiende hasta su tamaño anterior ni se reconstruye desde el JSON seed. El seed queda disponible para diagnóstico; no sustituye a un head perdido.

Una cola con PREPARE íntegro y COMMIT vacío puede resolverse sólo desde intención anterior válida y observación actual. Una cola con COMMIT no-cero inválido mantiene gate cerrado hasta resolución causal independiente. Daño dentro de la cadena, forks, reordenación o ausencia de un slot anteriormente referenciado bloquean siempre. No existe política de «quedarse con el prefijo y seguir» ni garantía de detección de corrupción arbitraria capaz de falsificar hashes.

`CloseHandle` es la liberación de un handle y debe llamarse una vez; la política de uncertainty ante interrupción es propia del proyecto, no una nueva garantía de Windows. El resultado durable y el resultado de cleanup son independientes. [Microsoft: CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle).

### 4.6 Garantías y límites verificables

**Crash de proceso:** exclusión de kernel, slots anteriores inmutables, intención antes del efecto, sello completo e idempotencia permiten reconstruir sin repetir efectos acreditados. Pruebas con subprocess termination son implementables ahora. No sustituyen un crash de host.

**Crash de host o corte de alimentación:** el contrato depende de NTFS local, barreras exitosas y hardware que honre flush/write-through. Microsoft documenta flush de metadatos relacionado con write-through y advierte que algunos discos no lo soportan. Ésta es una base de diseño condicionada, no una prueba de nuestro host. [Microsoft: caching de CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

No se invoca `FlushFileBuffers(directory)` como supuesto fsync POSIX. No se afirma atomicidad conjunta de journal, rename de VHDX y montaje WSL. El bootstrap crea nombres y sigue teniendo esa frontera de persistencia. Pérdida del journal tras reinicio exige `UNKNOWN` y conservación del final, nunca adopción por SHA/path. Un ACK sólo afirma barreras e identidad observadas bajo el contrato; no inmunidad ante firmware, pérdida física o corrupción arbitraria.

La publicación registra identidad previa al rename y llama `FlushFileBuffers` sobre el mismo handle después de NOREPLACE, sin alterar contenido sellado. Este flush no se presenta como fsync del directorio. La garantía de rename durable se verifica aparte; un flush que falle deja unknown. NOREPLACE sólo prueba no-clobber, no persistencia absoluta del namespace.

| Tipo de fallo | Garantía del diseño | Evidencia necesaria |
|---|---|---|
| Hijo/proceso terminado, host sigue vivo | Exclusión liberada por kernel; intención/slots válidos permiten replay idempotente y reacreditación | Crash cutpoints CPU NT reales |
| Excepción con proceso vivo | Capacidades quedan cerradas o inciertas; jamás se reusa un scalar incierto ni se repite el efecto por inferencia | Fault injection causal y testigos nativos de handles/archivos |
| Reinicio del host | Validar journal+disco actuales, no asumir continuidad del montaje ni leases; faltantes bloquean | Reinicio real de host, registro before/after y probes ext4/admin posteriores |
| Power loss | Durabilidad condicionada a NTFS, barreras y hardware. No se promete persistencia absoluta ni atomicidad multiobjeto | Ensayo específico de host/storage; los tests subprocess no cuentan |
| Medio corrupto o adversario fuera de frontera | Preservación y gate cerrado al detectar incoherencia; no certificación contra toda alteración posible | Alcance externo al contrato actual |

## 5. Impacto en módulos y ficheros

Estas rutas son propuestas concretas para el implementer, no modificaciones realizadas. Los nuevos archivos aparecen marcados como nuevos; los demás existen.

| Ruta | Cambio propuesto | Tipo |
|---|---|---|
| `scripts/storage_journal.py` | Codec acotado, slots, tokens, requests, snapshots y cadena | Nuevo |
| `scripts/storage_journal_windows.py` | Writer/reader por handle, creación exclusiva, ACL/identidad/parents, buffers alineados y flush | Nuevo |
| `scripts/storage_lifecycle.py` | Intents/completion, create/bootstrap/reconcile, validación y detach con gate | Nuevo |
| `scripts/storage.py` | Wiring explícito al controller; política/dry-run compatibles; gates admin y legacy | Modificado |
| `scripts/storage_attach.py` | Resolver journal y delegar efecto/commit; retirar writer por ruta; conservar parseo, planes y binding aceptado | Modificado |
| `scripts/storage_offline.py` | Registrar reserva/artefactos/fases con controller; JSON sólo export readonly | Modificado |
| `scripts/storage_publish.py` | Intent previo con incoming identity y completion durable; evitar writer JSON | Modificado |
| `scripts/storage.ps1` | Entrada Windows con entorno gestionado; no elevación automática | Modificado |
| `scripts/storage.sh` | Entrada readonly/plans y despliegue desde vista WSL acreditada; no impl Windows falsa | Modificado |
| `packages/storage-guard/studio_storage_guard/provision.py` | Auditor readonly separado para dominio ya provisionado, sin cambiar semántica new-empty ni reparación automática | Modificado aditivo |
| `tests/test_storage_journal.py` | Codec/requests/cadena/fases/compatibilidad | Nuevo |
| `tests/test_storage_journal_windows.py` | NT real: sharing, identidad, flush, races, close y crash CPU | Nuevo |
| `tests/test_storage_lifecycle.py` | Causalidad intents/resultados y recovery de artefactos privados; dobles de mount claramente identificados | Nuevo |
| `tests/test_storage_attach.py` | Wiring a journal/errores, sin atribuir montaje a doubles | Modificado |
| `tests/test_storage_offline.py`, `tests/test_storage_publish.py`, `tests/test_storage_preflight.py` | Cero caminos legacy con efectos, no-clobber e intenciones | Modificados |
| `packages/storage-guard/tests/test_provision.py` | Auditor existente, raíz nueva y provisión parcial preservada | Modificado |

No requiere modificación de `scripts/storage_receipt_store.py`, `tests/test_storage_receipt_store.py`, `scripts/storage_operator.py` ni `tests/test_storage_operator_binding.py`. Sus garantías se consumen, no se amplían retrospectivamente.

No exige cambiar schema de `StorageReceipt`, SQLite, Alembic, engines, GPU, locks de modelos/herramientas ni helper IPC aceptado. El wiring Compose existente conserva preflight por consumidor. Si la admisión de detach exige nuevas rutas de despliegue, ROOT debe liberar ese alcance por separado antes de habilitar detach.

**Vinculación canónica:** ADR-0075, el índice de decisiones, `storage-execution-design.md` y `docs/arquitectura/datos.md` documentan esta elección. No cambia ningún principio constitucional ni acredita código o QA física.

**Enlaces canónicos:** `storage-durable-design.md` enlaza spec, plan y ADR-0075. Los campos `storage_durable_design:` de spec y plan devuelven al subdiseño. Su campo `design: design.md` conserva el diseño general de secuenciación M1.

### 5.1 Dependencias de los cambios de arquitectura

El cuadro describe dependencias técnicas para liberar módulos; no es un plan, ledger ni estimación.

| Frontera de implementación | Depende de | Salida que habilita la siguiente | Gate que conserva |
|---|---|---|---|
| Formato y modelo operativo | O2 elegida y revisión A/B documental | Codec/envelopes/tokens y casos de corrupción definidos | Sin writer ni efectos |
| Store nativo NT | Codec cerrado | Create/open/read/commit exclusivos y cutpoints NT demostrados | Sin adopción VHDX, WSL o GPU |
| Bootstrap y fases offline/publish | Store NT y objetos propios acreditados | Seed preservado, reserva, IDs previos al efecto y published completion | Destino SMOKE existente siempre CONFLICT para producción |
| Attach/reconcile | Published snapshot válido, store NT y asociación actual demostrada | Intención/resultados de sesión, sin writer JSON legacy | Admin real; montaje no acreditado por runner CPU |
| Validated/auditoría de dominios | Montaje propio y helper/probes de ADR-0071 | Roles y dominios actuales, limpieza real y fase v1 terminal | No reejecutar provisión new-empty sobre biblioteca usada |
| Detach/backup de imagen | Admisión serializada, namespaces acreditadas y quiesce/flush propio | Detached observado y disk preservado | Desconocidos/BUSY bloquean; no copy activo ni stop global |
| Wiring CLI/despliegue | Controller consistente y QA de cada frontera liberada | Un único writer autorizado; legacy readonly | Gate persistente T-05/M1 no se cierra con pruebas aisladas |

### 5.2 Criterios de verificación

| Evidencia | Criterios |
|---|---|
| Codec CPU | Rechazar versiones desconocidas, duplicate keys, longitudes adversarias, bool como generation, slots/forks/hashes inválidos; v1 exacto preservado |
| NT privado sin admin | FILE_CREATE falla contra archivo vacío/no vacío/directorio/link; volumen+ID+parents por handle; writer previo bloquea; writer rival/rename/delete/write fallan; links/reparse rechazados |
| CAS NT | Dos procesos con token mismo: sólo uno sella; perdedor STALE/BUSY sin efectos; misma request recupera mismo token; mismo ID distinto request rechaza |
| Fallos causales | RED antes del código para short write, error flush1/flush2, corrupción, postflush-beforeACK, interruption y close uncertainty; causas originales conservadas |
| Crash CPU real | Hijo propio terminado en cada barrera usando artefactos privados; reopen real y verificación de bytes/identidades, sin dependencia de exit simulado |
| Recuperación de publish CPU | Incoming privado creado NT y rename real NOREPLACE; crash entre intención/rename/completion; destino ajeno intacto; misma identidad recuperada, sustituto rechazado |
| Compatibilidad | Seed v1 exacto e intacto; lectores aceptados sin modificación; ausencia journal impide ejecución nueva; published binding usa snapshot histórico original |
| Cleanup | Handles propios vuelven a baseline; cierre no se reintenta tras uncertainty; no recursive delete ni limpieza por nombre/hash |
| Cobertura/revisión | Gate whole ≥80% de módulos nuevos/cambiados sin exclusiones; lentes frescas A/B/C sobre controller nativo; QA independiente según dev-cycle |
| Admin posterior real | VHDX nuevo de producción acreditado, ext4/UUID auténticos, helper/roles reales, startup bloqueado en negativos, WAV→FFmpeg→NOREPLACE→BD/ready |
| Recovery persistente posterior | Reboot/recreate, crash attach/validated/detach, replay, scopes own-only, namespaces/consumidores, detach/reattach y backup/restauración reales |

Un test CPU de `validated` con runner doble sólo prueba política. No demuestra NOREPLACE en ext4, correlación VHDX/WSL ni close de montaje. El SMOKE no completa evidencia de producción. T-05 y sus verificaciones de worker/manifiesto siguen abiertos hasta sus gates reales.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Hardware no honra barreras o bootstrap pierde nombre | No medida | Autoridad perdida tras power loss | Contrato condicional; pruebas host aparte; gate UNKNOWN, conservar disco |
| Alineación NT o write-through no acreditados | Media hasta probe | Commit no confiable | Queries NT11/17 y política G2 de ADR-0078 aceptada por ROOT tras revisión/QA documental; writer reacredita buffers y modos; abortar sin fallback |
| Cola rota indistinguible de corrupción histórica | Media en fallo | Replay inseguro | No saltar ni truncar; bloquea cuando falta resolución causal verificable |
| Library usada llega a provisión new-empty | Alta si se repite API actual | Pérdida o bloqueo permanente | Auditor readonly separado, nunca chown-R/reformat/cleanup |
| JSON v1 writable antiguo sigue disponible | Alta durante wiring | Dos autoridades divergen | Corte coordinado de todos los entrypoints; legacy readonly y gate journal |
| Admission/detach omite Docker namespace o consumidor | Media | Desmontar biblioteca usada | Gate trusted deployer; snapshot IDs reales; rechazar unknown; no liberar detach hasta QA nativa |
| File ID se reutiliza después de borrar y recrear | Baja no medida | Falsa recuperación | Parents/política/reserva/historia y continuidad; ID no es prueba criptográfica de propiedad eterna; ambigüedad bloquea |
| Journal se llena | Previsible | No permite nuevos commits | Cuota explícita antes de efecto, no compactación ni overwrite improvisados |
| Cierre incierto oculta flush/efecto aceptado | Media en interrupción | Repetición o fuga de custodia | Resultado separado de cleanup, scalar invalidado, terminar owner antes de reabrir |
| Coste de pruebas nativas supera alcance previo | No recalculado | Falta de evidencia | ROOT conserva unidad acotada y gates; evaluator/planner revisan si hace falta, sin estimación aquí |

`FILE_ID_INFO` compara file ID y serial de volumen en un equipo. Lo empleamos con handles y política, nunca como certificado durable independiente. [Microsoft: FILE_ID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info).

## 7. Preguntas abiertas

1. Implementar y verificar el contrato de geometría NT11/17 ratificado en ADR-0078 mediante la unidad readonly; acreditar después write-through/no-buffering, buffers y DACL efectiva de la adquisición writer. Fallo bloquea O2 durable; no obliga a relajar custodia ni a reinterpretar FileStorageInfo Win32.
2. O2 fue elegida por ROOT y documentada en ADR-0075 tras revisión A/B. La implementación y las verificaciones reales siguen pendientes.
3. La continuidad de un objeto entre sesiones bajo el mismo SID depende de la frontera confiable declarada. Si se pide resistencia al mismo-SID hostil, haría falta autoridad protegida adicional y otro diseño.
4. El recovery de provisión ext4 incompleta requiere evidencia de entradas creadas propias. Sin ese contrato, el resultado correcto es preservar y bloquear.
5. Attach/dispositivo y exclusión de todos los consumers/namespaces para detach necesitan QA admin real. El diseño no convierte la diferencia `lsblk` o un UUID aislado en una garantía universal de asociación.
6. No se activa rollover del journal ni migración/adopción del SMOKE. Producción en el destino ocupado requiere decisión explícita de preservación y provisión nueva, fuera de esta ejecución privada.

La implementación CPU puede empezar por codec y leases NT nuevas tras la revisión documental que ROOT requiere. Estas incógnitas no justifican inventar un montaje o modificar componentes aceptados.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-11 | Tres opciones y O2 elegida por ROOT; aprobación privada, ADR propuesta y adopción canónica pendiente A/B |
| 2026-10-11 | Invariantes J01–J10, cutpoints C0–C7, compatibilidad exacta, límites de corrupción/power loss y dependencias de módulos concretados |


## Formato del journal v1 — unidad U1

Formato ratificado por ROOT bajo la delegación del propietario. La validación del codec es lógica y portable; la autoridad por handles, las barreras de disco y los efectos pertenecen al store y al controller posteriores.

### W1 · cabecera, endian y alineación

LE explícito mediante `struct`, nunca tamaño/orden nativo. Versiones independientes journal1/receipt1. `B` potencia de2 entre512 y65536 inclusive; CPU recibe B explícito para pruebas. El contrato G2 de U2b2/ADR-0078 elegido por ROOT deriva sólo B candidato de NT11/17: máximo de cuatro tamaños NT y mask+1 tras validación, divisibilidad de todos los requisitos, flags1/2 corroborados y offsets conocidos cero; unknowns o fuera de límite→bloqueo, sin escoger4096 por costumbre. El writer debe reacreditar geometría y buffers en su propia adquisición; candidato readonly no concede capacidad. No cambia el wire U1 ni amplía sus límites para acomodar un host.

Cabecera física ocupa B bytes: `magic[8]=MSJNL001`, `version:u32=1`, `header_bytes:u32=B`, `alignment:u32=B`, `slot_count:u32=64`, `max_payload:u32=1048576`, `reserved:u32=0`, `slot_bytes:u64`, `capacity_bytes:u64`, `journal_id[16]` (UUID bytes RFC4122 canónico), `header_sha256[32]`, resto cero. Campos suman96bytes. Hash: SHA256 de domain bytes ASCII `MSJNL/HEADER/v1` seguidos de cabecera completa B con campo digest cero. Desconocidos/reservados/padding no cero rechazan; EOF debe igualar capacity exacta.

No se asume que B ni un sector se escribe atómicamente. Versión/tamaño/digest/padding permiten detectar inconsistencias dentro del contrato, no todo adversario capaz de recomputar hashes. UUID journal distinto de UUID ext4; nunca generado por codec.

### W2 · 64 slots y layout exacto

`P=ceil(1048576/B)*B`; `S=B+P+B`; `capacity=B+64*S`. Slot i empieza `B+i*S`, i0..63. PREPARE header ocupa B; área payload P; COMMIT ocupa B distinto. Con B4096: P1048576, S1056768, EOF67637248bytes (64,50390625MiB). El store escribe cero real/reserva toda capacidad antes de efectos; pure codec no reserva ni crea archivo.

Payload real ≤1MiB **incluye todo envelope**, recibo y published snapshot codificados; exceder límite rechaza antes de allocation/slot. JSON embedded base64 reduce capacidad útil; no prometer seed1MiB+published1MiB en un envelope1MiB. Sin truncar, comprimir, streams alternativos, sparse, expansión ni rollover. Guardar datos pequeños de infraestructura; si no caben→PAYLOAD_TOO_LARGE y gate cerrado.

### W3 · PREPARE y COMMIT

PREPARE header: `magic[8]=MSPREP01`, `version:u32=1`, `frame_bytes:u32=B+P`, `slot_index:u32`, `reserved:u32=0`, `generation:u64`, `payload_length:u32`, `reserved2:u32=0`, `journal_id[16]`, `previous_commit_sha256[32]`, `request_sha256[32]`, `prepare_sha256[32]`, resto cero (152bytes de campos). Área payload tiene exactamente payload_length bytes seguida de ceros hasta P. Digest SHA256(domain `MSJNL/PREPARE/v1` + header completo con digest cero + área P completa). Incluye tipo/version/index/length/padding, no sólo JSON.

COMMIT: `magic[8]=MSCMIT01`, `version:u32=1`, `frame_bytes:u32=B`, `slot_index:u32`, `reserved:u32=0`, `generation:u64`, `journal_id[16]`, `previous_commit_sha256[32]`, `prepare_sha256[32]`, `request_sha256[32]`, `commit_sha256[32]`, resto cero (176bytes de campos). Digest SHA256(domain `MSJNL/COMMIT/v1` + B completo con digest cero). Todos campos compartidos concuerdan exactamente. COMMIT sin PREPARE válido rechaza. U2, no U1, realiza PREPARE→flush1/relectura→COMMIT→flush2/relectura→ACK.

### W4 · envelope JSON y bytes v1

UTF8 estricto sin BOM, canonical `json.dumps(ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)` + LF. Parser detecta duplicate keys recursivamente ANTES de construir dicts utilizables, rechaza NaN/Infinity, floats para números enteros, unpaired surrogates y trailing bytes. Reencode idéntico requerido. Máximo profundidad16, listas64 y strings32768 caracteres, salvo los campos base64 con límite derivado payload. Contador de nodos4096; enteros ≤u64 y no negativos donde proceda. Ninguna lista/depth arbitraria llega a recursión o allocations ilimitadas.

Schema envelope cerrado: `journal_version`, `generation`, `slot_index`, `journal_id`, `operation_id`, `request_id`, `request_payload_b64`, `request_sha256`, `previous_commit_sha256`, `receipt_payload_b64`, `receipt_sha256`, `published_receipt_payload_b64` (null antes published), `journal_identity`, `project_identity`, `parent_chain`, `owned_objects`, `intent`, `session`, `result`. No claves desconocidas. La primera unidad debe definir schemas cerrados de esos objetos, no aceptar `dict[str,object]` sin validar.

Propuesta mínima metadata wire: identidad `{volume_serial:u64,file_id:hex32,path:str,kind:'file'|'directory'}`; parent_chain lista de identidades directory ordenadas root→padre de journal, sin duplicados ni ciclos; owned_objects lista `{role,identity,parent_identity,name,origin}` con role enum journal/raw/incoming/published, origin enum created/reserved. Hashes son hex64 lowercase; file_id hex32 lowercase. Metadata no contiene handles/PIDs/FDs reutilizables, y **no prueba** policy/ACL/custodia. U2 la contrasta con realidad.

`intent`: null o `{action,request_id,previous_state,object_roles}`; actions enum reserve/raw_verify/vhdx_verify/publish/attach/validate/quiesce/detach/reconcile. `session`: `{epoch:u64,state,admission:'closed'|'open',distro:str|null,mountpoint:str|null}`; state enum inactive/attach_intent/attached/validate_intent/validated/quiesce_intent/detach_intent/detached/unknown. Admission open sólo con state validated, sin intent pendiente/result unknown; esto es consistencia de datos, nunca permiso de arrancar producto. `result`: null o `{state:'observed'|'unknown',code:str,causes:[str]}`; causas acotadas y sin secretos. Evidence nativa detallada, cookies de admisión y resoluciones causales no se improvisan en extras: ROOT debe cerrar schema adicional antes de U3–U5; hasta entonces no habilitar efectos que requieran esos campos.

IDs `operation_id` y `request_id`: ULID canónico Crockford uppercase26 con primera cifra0..7 y alfabeto válido (no I/L/O/U); journal UUID canónico lowercase, versión4/variantRFC4122. Exigir operation igual a recibo; journal UUID igual a header/frames, distinta de ext4 cuando presente. UUID ext4 canónico distinto se valida, no se sintetiza.

Windows paths: PureWindowsPath, drive local canónico `C:/…` sin UNC/device namespaces, relativo, ADS/colon fuera drive, NUL/control, backslash en representación wire, `..`, `.`, componentes vacíos, trailing espacio/punto ni nombres dispositivos reservados. Rechazar alias por comparación casefold además de path exacto wire. Recibo disk_path debe ser project path + `/data/_storage/studio-data.vhdx`; journal path + `/data/_storage/storage-control.journal`. Session mountpoint POSIX absoluto canónico, no `//`, `.`/`..`/NUL/control/backslash; plantilla permitida debe cerrarla ROOT antes de attach. Parseo paths no resuelve links ni afirma pertenencia nativa.

Bytes v1 van base64 estándar estricto (`validate=True`, reencode idéntico, sin whitespace). `receipt_payload_b64` es canonical v1 exacto, hash sobre bytes decodificados completos con LF. Validar JSON v1 estricto/duplicatekeys recursivo y preservar fases/history/campos existentes sin cambiar módulo aceptado. **Seam portable obligatorio:** `StorageReceipt.from_bytes` usa `Path.is_absolute()` del OS y no valida un `C:/…` en Linux. U1 valida wire Windows mediante `PureWindowsPath` y comprobación propia del contrato v1; no delega esa frontera al parser dependiente del host ni convierte path al Linux local. U2 Windows puede producir la proyección `StorageReceipt` aceptada después de validar bytes. Golden compartido y comparación en Windows con parser existente prueban compatibilidad; Linux verifica los mismos bytes con codec portable. Snapshot seed histórico si no es canonical no se reescribe: conservar como fuente aparte readonly; bootstrap necesita política explícita ROOT sobre bytes seed exactos, no normalización silenciosa. `published_receipt_payload_b64` queda exactamente igual en generaciones posteriores, phase published y history prefijo exacto de current v1. En attach/session v1 no se retrocede ni reescribe evidencia previa. Schema de evidence v1 se respeta; campos extensibles aceptados actuales se validan por fase/tipos/paths, sin inventar ampliaciones del recibo.

### W5 · cadena, incompletos y full

Generation inicial1 en slot0, predecessor zero32; después +1, mismo journal/operation. Slots usados inmutables y nunca reutilizados. Layout se inspecciona entero, no elegir máximo mtime/nombre ni primer prefix con hash válido. Todos ceros en slots restantes significa unused. Cualquier byte no cero detrás de unused gap, generación duplicada, fork, predecessor errado, slot index falso, cambio journal/operation/request o daño interior→JOURNAL_CORRUPT. EOF/header parcial→JOURNAL_CORRUPT_OR_UNKNOWN, nunca ampliar/reconstruir.

PREPARE íntegro + COMMIT todo cero en última cola→`incomplete_tail`, con bytes/slot observado y admisión bloqueada, sin head operativo utilizable para efecto. PREPARE parcial/nonzero o COMMIT no-cero inválido→unknown/corrupt bloqueante. No asumir que es sólo crash reciente: daño de commit previo puede parecer incompleto. Una inspección limpia sólo expresa integridad estructural observada; U2/U3 reacreditan historia/intención/realidad antes de operar. Codec no salta cola, no genera resolución ni sucesor tras gap. Resolución causal independiente de cola se diseña/prueba en unidad posterior; hasta release ROOT ese camino rechaza. `JOURNAL_FULL` al consumir64slots antes de nuevo efecto, incluye slots inciertos; request exacta ya sellada puede replay aun lleno.

### W6 · request conflict y replay

`request_payload_b64` conserva bytes canonical de objeto cerrado `{action,operation_id,arguments}`; ROOT cierra argumentos por action antes de U3. U1 soporta argumentos mínimos sin efectos de reserve (size_bytes,project_path) y record (phase,receipt_sha256); otras variantes sin schema ratificado rechazan explícitamente. Digest SHA256(domain `MSJNL/REQUEST/v1` + u32LE longitud + bytes); no hash de repr/dict.

Buscar request_id en TODA cadena íntegra antes de CAS de head: mismo ID/mismos bytes y digest→replay mismo commit lógico, sin slot adicional; ID repetido con bytes distintos aunque hash provisto igual→REQUEST_CONFLICT. Request ID duplicado en dos commits físicos→corrupción (writer idempotente no debería sellarlo otra vez). Token/head viejo sin request sellada→STALE_GENERATION. Intent y completion son requests separadas, completion referencia intent en schema futuro; no reutilizar un request ID con payload distinto para avanzar. Missing/blocked chain jamás replay operativo. Token nativo de U2 seguirá obligatorio; resultado replay puro no es ACK durable (requiere reopen/revalidate/flush U2).


La cadena de padres va desde la raíz de la unidad hasta el padre del journal, con pasos de hijo inmediato; incluye una vez la identidad del proyecto, permanece en el mismo volumen y rechaza aliases. La raíz C:/ sólo aparece como ancestro de directorio. En request record, phase y receipt_sha256 coinciden con el recibo actual y el SHA de sus bytes completos con LF; en reserve, size_bytes y project_path coinciden con el recibo actual.


### API lógica de U1

El módulo `scripts/storage_journal.py` contiene exclusivamente el codec portable. Sus dataclasses `JournalLayout`, `JournalHeader`, `JournalSnapshot`, `JournalHead`, `JournalInspection` y `RequestDecision` son frozen. La proyección de un snapshot devuelve una copia nueva; sus bytes y hashes permanecen exactos. Un head lógico construido por el caller nunca concede autoridad nativa.

| Función | Frontera |
|---|---|
| `encode_header(header)` / `decode_header(raw)` | Cabecera wire; encode admite JournalHeader o la tupla inmutable `(alignment,journal_id)` |
| `validate_snapshot(raw)` | Envelope y recibos exactos, tipos y límites cerrados; devuelve snapshot lógico |
| `request_sha256(raw)` | Digest por dominio de bytes; calcularlo no acredita la validez de la request |
| `encode_prepare(header,snapshot)` / `encode_commit(header,snapshot,prepare)` | Frames y padding de W3, sin escribir ni hacer flush |
| `inspect_journal(raw)` | Examina cabecera y todos los slots; corrupto o incompleto no devuelve head operativo |
| `decide_request(inspection,request_id,request_payload,expected_head)` | Replay exacto, conflict, stale o full; no ACK durable ni efecto |

Los inputs wire exigen bytes inmutables exactos. La admisión de una sesión en sus metadatos sólo expresa coherencia estructural; el store y el controller deben reacreditar identidad, política y estado real antes de cualquier operación. Requests futuras y resolución causal continúan deshabilitadas hasta cerrar sus contratos.


## Concreción del store Windows — organización O2 incorporada

[Diseño del store](storage-journal-store-design.md) y [ADR-0081](../../decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md), incorporados por ROOT tras revisión2 y QA95checks, separan kernel I/O privado de autoridad CAS/ACK. Preservan codec U1 y observación U2 readonly; la geometría U2b2 ya está incorporada en su componente, sin capacidad de writer. S1 completo, modo/buffers/revalidación y barreras son requisitos propios de la adquisición writable.

Bootstrap legacy, lifecycle, resolución causal de colas bloqueadas y ext4 persistente siguen unidades necesarias para el producto completo. El store clasifica/preserva incertidumbre y reacredita requests selladas; no salta colas ni entrega ACK desde un hash. No hay código/store nuevo, pruebas nativas, provisión ni aceptación de T05/M1 por esta adopción documental.
