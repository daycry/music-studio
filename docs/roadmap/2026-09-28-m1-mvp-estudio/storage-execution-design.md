# Ejecutor de almacenamiento: concreción de ADR-0069

Fecha: 2026-10-09. Elección de implementación por Root bajo delegación:
**B, preparar ext4 offline en archivos propios y convertir a VHDX**.
Diseño aprobado para implementar; las pruebas de custodia y conversión siguen
pendientes. No se ha creado ni montado un disco del estudio.

Se conserva [ADR-0069](../../decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md):
archivo físico `data/_storage/studio-data.vhdx`, biblioteca nueva, montaje como
vista virtual, producto en Docker, sin adopción/migración automática ni pérdida
de atomicidad. Ollama mantiene su excepción WSL compartida.

| Alternativa dentro de O2 | Complejidad/riesgo | Decisión |
|---|---|---|
| A: crear VHDX, attach y formatear dispositivo Linux correlacionado | Altos; falta asociación demostrada entre handle Windows y `/dev/*` WSL | No implementar primero; enumeración/tamaño/diferencia de listas no autorizan formato |
| B: ext4 offline sobre FD de archivo nuevo propio, conversión VHDX y attach por ruta exacta | Medios, condicionados a probes reales de las herramientas y custodia Windows/Linux | Elegida; evita formatear un dispositivo Linux elegido por posición |

`GetVirtualDiskPhysicalPath` identifica el dispositivo Windows desde un handle;
no prueba su correspondencia con un nombre de dispositivo Linux.
[API Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/virtdisk/nf-virtdisk-getvirtualdiskphysicalpath).

## Preparación, publicación y custodia

Reservar un directorio temporal propio exclusivo dentro del proyecto. Retener
handles de ancestros/archivos Windows, identidad VolumeSerialNumber+FileId y
protección contra reparse, hardlinks, rename y delete. Crear raw y salida
temporal exclusivamente; el ejecutor Linux conserva FDs propios de archivos
regulares. `mke2fs` y QEMU escribirán a esos FDs heredados, sin rutas finales
ni dispositivos enumerados. Deben comprobarse en pruebas reales la identidad
y compatibilidad de los guardianes Windows con los accesos WSL/Docker.
[Identidad](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info).

La exclusividad pertenece al executor: QEMU no la proporciona al crear su
archivo. El uso de `/proc/self/fd/<n>` es candidato respaldado por lectura del
código, todavía pendiente de prueba con la versión fijada. Crear primero un
VHDX válido en el FD temporal y convertir con `-n` hacia ese mismo destino;
`-n` no inicializa un archivo vacío. Prohibidos `-U`, `--salvage` y
`--target-is-zero` sin acreditar ceros. `-add-fd` de qemu-system no se atribuye
a qemu-img. [Manual QEMU](https://www.qemu.org/docs/master/tools/qemu-img.html),
[código de apertura](https://raw.githubusercontent.com/qemu/qemu/v10.0.0/util/osdep.c).

Validar ext4 offline con UUID seleccionado y configuración compatible explícita;
`e2fsck` no reparará automáticamente. Promover el VHDX final por handle Windows
con ReplaceIfExists=FALSE. Cualquier destino existente se conserva, incluso
vacío: no rename ordinario como fallback.
[Rename por handle](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info).

## Permisos y recuperación

La preparación offline no requiere administrador Windows. Attach/detach por
WSL sí requieren privilegio de plataforma. Usar exclusivamente ruta acreditada
y nombre de montaje propio; nunca omitir argumento de unmount ni detener WSL,
Docker u Ollama globalmente. [Montaje WSL](https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk).

Registrar fases durables reserved→raw_verified→vhdx_verified→published→attached→validated,
identidades propias, UUID, tamaño y herramientas fijadas. Tras crash, startup
permanece bloqueado hasta acreditar artefactos propios; no adoptar por nombre
o hash. Un final publicado se conserva aunque falle attach. Su checksum inicial
no es identidad permanente, porque cambia durante el uso. Detach exige
quiesce/flush de consumidores propios y falla si están ocupados.

## Preflight de cada consumidor

**Actualización vigente:** [ADR-0071](../../decisiones/ADR-0071-probes-de-almacenamiento-en-dominio-aislado.md)
separa inspección local y prueba en helper CPU aislado, después de los hallazgos
de review1. La limpieza directa en una raíz compartida descrita en el primer
componente no está aceptada. B02/B03 y dominio se implementan primero; IPC,
provisión y wiring siguen como unidades posteriores verificables.

Módulo compartido sin torch, dispositivos ni privilegios. Abrir directorios
con O_DIRECTORY|O_NOFOLLOW, retener FD/identidad, consultar UUID real por FD,
relacionar entrada exacta de mountinfo y comprobar ext4/opciones/raíces:

| Consumidor | Montaje |
|---|---|
| Server | `/data`, mount_root `/`, RW |
| Engine biblioteca | `/data`, mount_root `/`, RO deliberado |
| Engine crudos | `/data/tmp`, mount_root `/tmp`, RW y mismo UUID |

No exigir RW indiscriminadamente a la biblioteca de los engines. En el subárbol
escribible autorizado, crear únicamente un directorio aleatorio propio y probar
NOREPLACE contra destino ausente y testigos propios vacío/no vacío/archivo/enlace.
Verificar preservación y limpiar sólo objetos acreditados. Error UUID/mount/IOCTL/
NOREPLACE aborta antes de logs, migración, cola o importación de torch.

El arquitecto observó el host con administrador Windows False, WSL2.7.14.0,
kernel6.18.33.2 y UID1000. Su probe de sólo lectura FS_IOC_GETFSUUID sobre `/`
tuvo éxito con longitud16; demuestra capacidad del kernel, no identidad de un
VHDX propio ni funcionamiento en contenedores del estudio. Request x86_64
0x80111500, struct fsuuid2 de17 bytes; el código Linux no exige CAP_SYS_ADMIN.
[Linux v6.18](https://raw.githubusercontent.com/torvalds/linux/v6.18/fs/ioctl.c).
Es una observación del arquitecto; Root no inventa un recibo CLI separado.

Hooks reales: server lifespan antes de configure_logging/migrate; ACE entrypoint
antes de importar torch; analysis/mock antes de Uvicorn. Gate dentro de cada
consumidor. Verificar después que Compose desde WSL expone el VHDX como ext4
real; la recomendación documental no prueba ese despliegue.
[Docker WSL](https://docs.docker.com/desktop/features/wsl/best-practices/).

## Trabajo pendiente y alcance de los tests

QEMU está ausente; e2fsprogs1.47.2 observado no sustituye herramientas del
proyecto fijadas/verificadas. Añadir filas legales y lock de origen/revisión/SHA/
dependencias antes de integrarlas. No se descargan ni incorporan binarios por
esta aprobación de diseño. Preferencia: herramientas en contenedor CPU propio,
con paquetes/imagen fijados, sin loop, privilegios ni socket Docker interno.
[e2fsprogs](https://raw.githubusercontent.com/tytso/e2fsprogs/v1.47.2/misc/mke2fs.c).

Módulos: `scripts/storage_windows.py`, `scripts/storage_offline.py` y paquete
`storage-guard` con `verify_root→RootLease`. El executor offline ya prepara y
verifica el raw/VHDX temporal con recibo hasta `vhdx_verified`; `scripts/storage.py`
se conserva como política para las operaciones finales. Promoción por handle,
attach/mount, wiring de Compose y los wrappers de consumidor siguen pendientes
de pruebas nativas. Los locks y Dockerfiles se coordinan con el worker de audio.

### Resultado del diagnóstico FD: custodia Windows indispensable

Los seis controles reales del diagnóstico `t05-storage-tool-fd-debug1`
aislaron una limitación del bind9p Windows de esta máquina. Sin renombrar,
fstat/getsize ven64MiB. Después de renombrar, fstat/reopen del FD devuelven
ENOENT; sustituyendo el nombre original por un testigo de45bytes, fstat y
el reopen de `/proc/self/fd` observan tamaño45 y mke2fs calcula cero bloques.
El pread del FD original y del reopen no observan necesariamente los mismos
bytes. No basta conservar dev/ino ni interpretar el fallo como flags de mke2fs.
Los mismos controles tmpfs conservan64MiB; no son prueba de persistencia.

Root verificó142artefactos y la matriz de seis controles; recibo
`t05-storage-tool-root1/root-fd-cause-verification.json`. La preparación de
herramientas y los controles tienen imagen/paquetes fijados. No se ha aplicado
un fix ni acreditado conversión segura.

Se mantiene la exigencia original de guardianes Windows: el siguiente probe
privado retiene identidad FILE_ID_INFO y handles sin FILE_SHARE_DELETE en
archivo/ancestros mientras el hijo Linux usa sus FDs. Debe demostrar primero
que rename/delete se rechazan y que FD/identidad/bytes siguen siendo propios;
después prueba mke2fs/QEMU sobre los mismos FDs. Si impide acceso/escritura
necesaria, se conserva el fallo. No se retira protección para obtener verde,
no se pasan bloques explícitos para ocultar el tamaño reatado, ni se adopta
tmpfs como preparación persistente. Provisión final y promoción por handle
siguen pendientes de pruebas propias.

RED conductual antes de producto: destinos ajenos intactos, alias/hardlink/
reparse/races rechazados; conversión sigue escribiendo sólo FD propio si cambian
nombres; crash no permite adoptar/reformatear; montajes incorrectos y fallo
NOREPLACE impiden startup. Sin admin: custodia de archivos y preparación/conversión
fijadas. Con admin: VHDX propio real, consumidores compartidos, audio/publicación,
crash/replay, reinicio, detach/reattach y backup/restauración. Los primeros no
sustituyen los segundos ni cierran T-05.


## Controller durable elegido

El [diseño del ciclo durable](storage-durable-design.md) y [ADR-0075](../../decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md) concretan O2: journal estable por handle, generaciones PREPARE/COMMIT, CAS e intenciones previas a los efectos. La fase v1 validated conserva su historia; sesiones separadas representan reattach/quiesce/detach. El writer exclusivo relee y reacredita autoridad; el seed readonly no sustituye al head vigente.

La elección no acredita implementación ni almacenamiento persistente. Se conserva el VHDX SMOKE existente y la provisión no se repite sobre una biblioteca usada. Attach, montaje/UUID, validated y detach requieren comprobación real de plataforma; dobles CPU y flush de un archivo no acreditan esos efectos.
