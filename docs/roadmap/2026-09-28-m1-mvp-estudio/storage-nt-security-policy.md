---
policy: storage-nt-security-s1
titulo: Admisión estricta del dominio y cadena del journal NT
estado: aprobado
fecha: 2026-10-11
elegida_por: ROOT bajo delegación vigente del propietario
opcion: S1
revision_documental: A/B conforme, intento 1; aceptación documental de ROOT
implementacion: no liberada por este documento
design: storage-durable-design.md
adr: ../../decisiones/ADR-0076-politica-estricta-de-confianza-del-journal-windows.md
---

# Política NT — Admisión estricta del dominio y su cadena

ROOT eligió **S1** bajo la delegación vigente del propietario. Esta política concreta G2 de [ADR-0075](../../decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md) y del [diseño durable](storage-durable-design.md), sin cambiar O2, el codec ni el wire W1–W6. La excepción de owner del ancla del sistema se registra en [ADR-0076](../../decisiones/ADR-0076-politica-estricta-de-confianza-del-journal-windows.md).

La elección documental no acredita implementación, ABI, host, almacenamiento de producción o M1. Una cadena que no cumple la política mantiene admisión cerrada. No se cambian ACL existentes para obtener un positivo.

## Frontera de confianza y principal

El deployer del host, el principal Windows autorizado, SYSTEM y administradores conservan la frontera de ADR-0075. No se promete resistencia a un administrador, a sus privilegios de restore/toma de propiedad ni a código malicioso con el mismo SID. Se conserva el supuesto de controller confiable; esta política no demuestra que el despliegue actual impida toda modificación de su código.

El deployer acredita el principal antes de abrir objetos candidatos. El controller consulta el SID binario válido de su contexto efectivo autorizado; una impersonación no ratificada rechaza. No deriva el principal del owner de la ruta, del journal, de grupos del token ni de un nombre de cuenta. No fija el SID personal de un host en código público o plantillas.

SYSTEM y Administrators se identifican por sus SIDs well-known exactos mediante mecanismos Windows. Nombres localizados, prefijos SID o traducciones exitosas no amplían la allowlist. Un grupo adicional o un SID sin resolver permanece outsider. [Microsoft: Security identifiers](https://learn.microsoft.com/en-us/windows/win32/secauthz/security-identifiers).

## Roles, owner y trustees permitidos

| Papel | Owner admitido | Trustees de mutación admitidos |
|---|---|---|
| Journal y dominio nuevo | Exactamente el principal autorizado | Principal autorizado, SYSTEM y Administrators |
| Padres existentes, incluido proyecto | Principal autorizado, SYSTEM o Administrators | Principal autorizado, SYSTEM y Administrators |
| Root real del volumen del sistema Windows | Los anteriores o excepción exacta TrustedInstaller acreditada | Los tres ordinarios; TrustedInstaller sólo obtiene su control implícito de owner en ese root |

La excepción **TrustedInstaller sólo se aplica al owner del root real del volumen del sistema**. El actor acredita el SID binario de la cuenta de servicio Windows `NT SERVICE\TrustedInstaller`, compara igualdad exacta y demuestra el papel del handle del root. No aplica a `Users`, perfil, proyecto, padres interiores, dominio ni journal. No acepta cualquier `S-1-5-80-*`, otro servicio, otro root o una cadena que sólo muestre ese nombre.

La cuenta de servicio se acredita mediante los mecanismos Windows de nombre de servicio↔SID; una consulta fallida o ambigua rechaza. La identificación del volumen del sistema procede del contexto Windows/deployer confiable, no del journal, una variable de entorno o la letra de unidad aislada. Nada habilita privilegios o modifica el servicio. [Microsoft: SERVICE_SID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info).

Owner se evalúa incluso si no hay ALLOW WRITE_DAC explícito: Windows le reconoce control implícito de la DACL. Owner outsider rechaza. La comparación con la allowlist no demuestra por sí sola origen propio ni bootstrap. [Microsoft: propietario de un objeto nuevo](https://learn.microsoft.com/en-us/windows/win32/secauthz/owner-of-a-new-object).

## Descriptor y ACE: condición suficiente cerrada

El controller consulta OWNER/GROUP/DACL por `GetSecurityInfo` sobre el mismo handle retenido, con READ_CONTROL real. Comprueba resultado, integridad y límites del descriptor, owner/SID, ACL/ACE y control de herencia. Libera el buffer según el contrato de la API. DACL ausente, NULL, corrupta o incompletamente interpretable rechaza. Una DACL vacía no concede acceso y no constituye positivo operativo. No solicita SACL ni activa privilegios para pasar. [Microsoft: GetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo).

La política acepta sólo ACE ALLOW/DENY estándar con SID binario válido, máscaras y flags interpretados completamente. Conserva orden y procedencia explícita/heredada. Rechaza DACL no canónica; no reordena, elimina ACE ni repara ACL existentes. ACE object, callback, conditional, compound u otro tipo no soportado rechaza **también si es inherit-only**. OWNER RIGHTS, CREATOR_OWNER y otros trustees genéricos no se sustituyen por el principal; sin semántica ratificada para el papel, rechazan.

| Elemento | Regla |
|---|---|
| INHERITED sin INHERIT_ONLY | ACE efectiva; recibe la misma clasificación que una explícita |
| INHERIT_ONLY | No controla el objeto actual; evaluar propagación al siguiente componente seleccionado |
| OBJECT_INHERIT, CONTAINER_INHERIT, NO_PROPAGATE | Interpretar según tipo de hijo; no convertir flag en derecho efectivo |
| Generic rights | Mapear a derechos específicos del papel archivo/directorio antes de clasificar; bit/máscara desconocidos rechazan |
| ALLOW efectivo outsider peligroso | Rechazo, aunque otro DENY parezca compensarlo |
| DENY | Conservar y respetar al adquirir acceso; no restar máscaras globalmente ni asumir qué grupos comparten todos los outsiders |
| SID no resuelto | Sigue presente y outsider; la traducción fallida no elimina sus grants |
| Grupos propios enabled/disabled/deny-only | Afectan acceso del token efectivo; no conceden confianza al grupo ni a otros miembros |

Windows procesa ACE en secuencia y utiliza trustees del token. S1 usa una condición suficiente conservadora: ausencia de ALLOW outsider peligroso efectivo. No inventa una evaluación universal de todos los tokens ni legitima un grant peligroso mediante otro DENY. [Microsoft: AccessCheck](https://learn.microsoft.com/en-us/windows/win32/secauthz/how-dacls-control-access-to-an-object), [atributos de grupos SID](https://learn.microsoft.com/en-us/windows/win32/secauthz/sid-attributes-in-an-access-token).

Las ACE inherit-only se interpretan, no se ignoran. Un grant heredable peligroso puede dejar de propagarse al hijo protegido, pero eso no borra su efecto en otro padre donde sea efectivo. Se consulta cada descriptor real de la cadena. [Microsoft: ACE_HEADER](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-dtyp/628ebb1d-c509-4ea0-a10f-77ef97ca4586), [herencia de ACE](https://learn.microsoft.com/en-us/windows/win32/secauthz/ace-inheritance-rules).

## Derechos peligrosos y namespace

| Objeto/papel | ALLOW outsider que impide admisión |
|---|---|
| Journal | WRITE_DATA, APPEND_DATA, WRITE_EA, WRITE_ATTRIBUTES, DELETE, WRITE_DAC, WRITE_OWNER; el descriptor cerrado nuevo sólo concede derechos a los tres trustees ordinarios |
| Dominio protegido | ADD_FILE, ADD_SUBDIRECTORY, WRITE_EA, WRITE_ATTRIBUTES, DELETE_CHILD, DELETE, WRITE_DAC, WRITE_OWNER |
| Cada padre exterior retenido | DELETE propio, DELETE_CHILD sobre el siguiente componente, WRITE_EA, WRITE_ATTRIBUTES, WRITE_DAC, WRITE_OWNER; owner outsider también rechaza |

Los nombres de derechos se interpretan según tipo de objeto: WRITE_DATA de archivo y ADD_FILE de directorio comparten bit, pero cumplen papeles distintos. READ/LIST/TRAVERSE/READ_ATTRIBUTES/READ_EA/READ_CONTROL/SYNCHRONIZE de outsiders pueden admitirse en el prefijo exterior cuando todos sus bits son conocidos y no introducen mutación. No se abren permisos nuevos para permitirlos. [Microsoft: derechos de archivo/directorio](https://learn.microsoft.com/en-us/windows/win32/wmisdk/file-and-directory-access-rights-constants).

ADD_FILE/ADD_SUBDIRECTORY en un padre exterior, incluido el root del sistema, puede crear siblings. No equivale por sí solo a sustituir el componente existente. Se admite únicamente con ausencia de los derechos peligrosos anteriores, owner acreditado, hijo existente retenido y apertura NOREPLACE si se crea el dominio. Nombre ocupado causa conflicto y conservación; nunca adopción. No se rechaza todo árbol Windows porque el root permita crear directorios a Authenticated Users.

DELETE del hijo **o** DELETE_CHILD del padre puede autorizar delete/rename. La DACL cerrada del hijo no anula DELETE_CHILD del padre. WRITE_DAC/WRITE_OWNER del padre puede ampliar ese riesgo. S1 rechaza esos grants de outsiders, sin confiar en que la lease los neutralice permanentemente. [Microsoft: DeleteFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-deletefilew).

Sharing e inspección de seguridad son complementarios. Retener sin SHARE_DELETE protege operaciones delete/rename acreditadas durante la lease, pero no inmoviliza DACL, owner, atributos o EA. Checks antes/después no prueban ausencia de un cambio transitorio ABA. Por eso S1 rechaza la autoridad outsider de mutación del prefijo; no usa pre/post como sustituto de la política. [Microsoft: CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

## Ancla, capacidades y creación cerrada

El bootstrap acredita primero el root real del volumen desde la frontera Windows/deployer y después cada padre desde su handle. La letra de unidad, path, owner aislado, file ID en JSON o digest no son el ancla. Se recorren nombres de un componente, sin reparse/alias ni reapertura por nombre para operar. `RootDirectory` permite apertura relativa; los flags no-follow y su binding user-mode requieren acreditación nativa de G1. [Microsoft: OBJECT_ATTRIBUTES](https://learn.microsoft.com/en-us/windows/win32/api/ntdef/ns-ntdef-_object_attributes).

Los ancestros retienen TRAVERSE, READ_ATTRIBUTES y READ_CONTROL reales sin SHARE_DELETE. Acceso cero/metadata-only no prueba exclusión. Journal writer retiene lectura/escritura real y sharing cero; read view usa READ y sólo SHARE_READ. Se comprueba sharing bilateral, incluyendo rivales abiertos antes. Revalidación conserva volumen/file ID, tipo, path canónico, reparse, link count, estado delete-pending, owner/DACL y cadena antes/después de cada frontera.

Crear exige `NtCreateFile(FILE_CREATE)`, descriptor cerrado **en la creación** y `Information=FILE_CREATED`. Owner es el principal ratificado; DACL presente protegida contiene sólo ALLOW explícitos ordinarios. No se crea con herencia abierta para cambiar ACL después. El descriptor propuesto no endurece objetos preexistentes. Todo hijo propio relevante recibe descriptor cerrado y revalidación. [Microsoft: NtCreateFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile), [SE_DACL_PROTECTED](https://learn.microsoft.com/en-us/windows/win32/secauthz/security-descriptor-control).

Abrir usa FILE_OPEN, sin crear si falta. Un objeto preexistente, incluso vacío o con bytes idénticos, no satisface una creación propia. Esta política no libera bootstrap legacy, seed SMOKE, VHDX, provisión o lifecycle. Capacidad parcial o fallo conserva objetos propios inciertos y cierra admisión; no borra ni reintenta por nombre.

Un snapshot U1, generación, UUID, SHA o `JournalHead` sólo acredita bytes/estructura. No crea OwnedFile, writer, JournalToken nativo o ACK durable. El writer relee por su handle y compara identidades actuales, padres, generación, digest y request bajo exclusión. Reinicio reacredita toda la cadena; no utiliza un token futuro imaginario ni actualiza historia para legitimar reemplazo. No hay nuevo binding/controller en esta unidad.

## Resultado del host y alcance de evidencia

S1 es implementable como política de rechazo sin remediar ACL existentes. Si los handles confirman los grants MODIFY outsider observados por nombre en workspace/`.cache`, corresponde **SECURITY_UNACCREDITED**, sin admisión ni efectos de producto. La observación por nombre no acredita el resultado nativo ni identifica las cuentas no resueltas como inexistentes. No se publican SIDs personales ni rutas del usuario en este documento.

SECURITY_UNACCREDITED conserva el diagnóstico de G2 ya establecido en el brief. Esta política no inventa enums, códigos HTTP, endpoints, clases o API pública; la futura implementación debe respetar los contratos de error existentes. Desconocido, inconsistencia o fallo de consulta siempre mantienen gate cerrado y revocan capacidad operativa antes de exponer el fallo.

**S2 sólo permite evidencia experimental de objetos nuevos durante una lease.** Un descriptor/handle de fixture positivo puede demostrar creación cerrada, parsing y exclusión del leaf. Si los padres no pasan S1, ese positivo es parcial: no acepta G2 completo, producción o restart. Las ACL adversarias se limitarían a objetos nuevos propios liberados por ROOT; ningún padre existente se muta.

**S3 queda aplazada.** Un dominio nuevo con padres exteriores mutables exige resolver replay de un árbol legítimo antiguo completo, asociación activa independiente, bootstrap/reparse y custodia del código. Owner/DACL/IDs autocontenidos pueden ser coherentes con ese árbol antiguo. No se implementan su binding, token o controller. Su viabilidad futura necesita otra decisión/ADR y evidencia; no se presenta como solución de esta unidad.

G0 está cerrado por freeze U1 aceptado por ROOT. Esta decisión sólo cierra la definición documental de S1 y su excepción exacta. G1, G2 nativo y las demás puertas conservan sus evidencias pendientes. Revisión A/B documental, release U2 y QA real siguen separadas. Ningún estado de tarea o de M1 cambia por este texto.
