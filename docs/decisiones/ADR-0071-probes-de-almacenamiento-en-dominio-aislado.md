# ADR-0071 · Probes de almacenamiento en un dominio aislado

- **Estado:** aceptada bajo delegación autónoma del propietario; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-09.
- **Relacionadas:** ADR-0007, ADR-0017, ADR-0069, ADR-0070.

## Motivo y alternativas

La revisión1 del nuevo storage-guard confirmó2Critical y2Important:
stat→unlink/rmdir permite borrar un objeto sustituido; el sello posterior al
cierre puede adoptar bytes concurrentes; la lease pierde binding de la ruta
original al mover el montaje y la adquisición raw puede devolver biblioteca
yaRW. Las reproducciones B/C en memoria y las fuentes quedaron congeladas;
no se acepta el componente por sus suites verdes.

Linux unlinkat no proporciona una eliminación condicionada al inode observado
por el stat del caller. Más comprobaciones o quarantine NOREPLACE no eliminan
la ventana posterior. [Código Linux6.18](https://raw.githubusercontent.com/torvalds/linux/v6.18/fs/namei.c).

| Opción | Consecuencia | Decisión |
|---|---|---|
| O1: dominio protegido antes de crear testigos, ejecución y limpieza aisladas | Conserva limpieza inmediata propia y preservación de objetos ajenos; requiere ABI/despliegue verificados | Elegida |
| O2: retener durante concurrencia y reclamar bajo exclusión real de plataforma | Requiere admisión limitada y recuperación efectiva; limpieza diferida explícita | Descartada como semántica principal |
| Quarantine y comprobación posterior, sin aislamiento | Sigue re-resolviendo nombres; puede mover o borrar sustitutos | Insuficiente como fix independiente |

El objetivo sigue incluyendo limpieza efectiva de lo propio. Una contención
que retenga residuos no se presenta como cumplimiento completo.

## Dominio POSIX y procesos

La plataforma prepara únicamente el ext4 nuevo de ADR-0069:

| Objeto | UID:GID | Modo |
|---|---|---|
| raíz DATA y tmp | `0:10001` | `1770` |
| DATA/.storage-probes y DATA/tmp/.storage-probes | `19000:10001` | `0700` |
| DATA/.storage-control | `19000:10001` | `0750` |
| socket guard.sock | `19000:10001` | `0660` |
| lock propio dentro del control | `19000:10001` | `0600` |

El sticky protege los nombres reservados en padres escribibles. El modo0700
por sí solo no impide renombrar una entrada desde un padre escribible.
Se rechazan owner/modo incorrectos, enlaces, ACL POSIX de acceso/default o
consulta de ACL no acreditada. No chown-R ni adopción/corrección silenciosa
de biblioteca existente. UID/modos9p no prueban esta política POSIX ext4.

Helper CPU Docker exclusivo `19000:10001`. Server/mock/ACE/analysis declaran
explícitamente `10001:10001`. Todos cap_dropALL y no-new-privileges; sus arranques
comprueban IDs reales/efectivos/saved, capacidades activas/permitted/inheritable
vacías y NoNewPrivs antes de producto/datos. El helper no recibe GPU, TCP,
socket Docker, dispositivos, loop ni SYS_ADMIN. La base CPU fijada se reutiliza.

La identidad19000 sólo pertenece al helper del estudio: no modelos/plugins,
procesos ajenos, exec durante operación, PIDnamespace compartido o FDs privados
expuestos. Host/controlador de despliegue son frontera confiable; no se promete
resistencia a un administrador que cambie el kernel o esa frontera.

## Prueba fresca sobre el montaje real

AF_UNIX pathname protegido, una solicitud acotada por conexión:

1. Consumidor abre y retiene la **ruta original solicitada**. Comprueba su
   UUID real, filesystem, mount ID local, root, identidad y RO/RW.
2. Conecta al socket protegido; SO_PEERCRED exige helperUID19000/GID10001.
   Genera challenge nuevo de32bytes y envía versión/rol cerrado/challenge
   más exactamente un FD raíz mediante SCM_RIGHTS.
3. Helper exige peerUID10001/GID10001, framing y ancillary estrictos,
   MSG_CMSG_CLOEXEC, sin truncamiento ni FDs extras. Cierra todo FD recibido
   incluso en error. No acepta una ruta del request para abrirla.
4. Compara el FD recibido contra su raíz propia allowlisted: UUID autorizado
   por su configuración, st_dev, st_ino, tipo y política. No adopta UUID del
   request ni compara mount IDs entre namespaces.
5. Abre `.storage-probes` desde **ese FD recibido**, valida su dominio y ejecuta
   un probe nuevo. Ningún FD de dominio/testigo sale al consumidor.
6. Sólo tras limpiar y revalidar responde versión/rol/challenge e identidad.
   Consumidor valida la respuesta y revalida sus rutas originales antes de
   obtener la lease. La adquisición raw termina revalidando library y raw;
   cualquier fallo libera ambas.

El FD recibido puede referirse a un mount ausente del mountinfo del helper:
se separan acreditación del objeto recibido e inspección local del namespace.
No se autentica por PID; puede no ser representable entre PIDnamespaces.
Mapeos UID/GID incompatibles/no acreditados bloquean la primera versión.

No recibos antiguos/cacheados, callerboolean, challenge discordante ni timeout
habilitan el gate. Helper secuencial, mensajes/conexiones acotados y deadlines;
segunda instancia confiable no limpia sockets antes de adquirir exclusión.
El lock coopera entre helpers confiables, no sustituye el dominio frente a10001.

## Creación, escritura y limpieza

El helper retiene FDs creadores; usa fstat antes de cerrar y contenido esperado
declarado de antemano, sin adoptar bytes posteriores. Los mkdir→open y deletes
ocurren dentro del dominio protegido desde antes de la creación. La limpieza
sigue por nombre: la garantía deriva de exclusión real, no de CASinode ficticio.
No elimina directorios permanentes ni residuos desconocidos por prefijo.

El consumidor RW acredita por separado archivo anónimo
O_TMPFILE|O_EXCL|O_RDWR|O_CLOEXEC: escribe patrón, fsync, relee, nlink0 y cierra.
No nombre visible ni unlink/rmdir; falta de soporte falla sin fallback nombrado.
LibraryRO no ejecuta escritura/probe. Esta prueba no sustituye publicación
mkdir/rename real bajo10001 ni políticas LSM.

Tras crash, residuos sin autoridad se conservan y bloquean éxito. Recuperación
automática requiere autoridad durable propia y protocolo explícito; no se
reconstruye propiedad por nombre/UID/hash observado después. Ese gate sigue
pendiente antes de aceptar persistencia.

## Implementación y puertas

Tres unidades coordinadas: dominio/primitivas y B02/B03; IPC/ABI; provisión y
wiring. Paquete stdlib, sin nuevas dependencias. Helper propuesto en
`apps/storage-guard/Dockerfile`; startup de cada consumidor antes de logs,
migraciones, cola y torch. Wrappers/Compose/provisioner fijan política real.

REDs nativos con rivales10001 y syscalls reales: sustituciones entre último
check/delete, origen modificado, mkdir→open, padres/noSticky/ACL/UID/caps,
fakeSocket, replay, FD errado/RO, ancillary extra/truncado, muerte/instancias,
ausencia de limpieza y residuos tras crash. Inyección puede programar barrera,
no sustituir el syscall verificado. CPU/tmpfs acredita sólo esas primitives;
VHDX ext4, permisos efectivos, namespaces Docker y recorrido completo T-05
bajo credenciales finales son gates adicionales. No se cierra T-05 por diseño.

Fuentes primarias: [sticky](https://man7.org/linux/man-pages/man7/inode.7.html),
[ACL Linux](https://raw.githubusercontent.com/torvalds/linux/v6.18/fs/posix_acl.c),
[AF_UNIX](https://man7.org/linux/man-pages/man7/unix.7.html),
[SO_PEERCRED kernel](https://raw.githubusercontent.com/torvalds/linux/v6.18/net/core/sock.c),
[socket Python3.12](https://docs.python.org/3.12/library/socket.html),
[O_TMPFILE](https://man7.org/linux/man-pages/man2/open.2.html),
[Docker userns](https://docs.docker.com/engine/security/userns-remap/).
