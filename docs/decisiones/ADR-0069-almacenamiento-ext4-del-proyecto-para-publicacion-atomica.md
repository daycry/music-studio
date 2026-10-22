# ADR-0069 · Almacenamiento ext4 del proyecto para publicación atómica

- **Estado:** aceptada bajo delegación autónoma del propietario; provisión, implementación y QA persistente pendientes.
- **Fecha:** 2026-10-09.
- **Relacionadas:** ADR-0005, ADR-0035, ADR-0053, ADR-0055 y ADR-0065.

## Evidencia y alternativas

El primer recorrido WAV→hijo propio→FFmpeg→paquete preparado falló al
publicar sobre el bind Windows de Docker Desktop. Dos probes propios
confirmaron 9p/DrvFS: source y destino comparten filesystem, pero
renameat2(RENAME_NOREPLACE) hacia destino ausente devuelve EINVAL. En tmpfs
nativo funciona. Un rename ordinario reemplaza un directorio ajeno vacío
en ambos filesystems; se descarta ese fallback.

O1, rename Windows por SMB2, conserva NTFS pero incorpora servicio,
credenciales y autoridad adicional de plataforma. O2, ext4 en VHDX del
proyecto, conserva el protocolo y los servicios existentes. O3, mkdir más
archivos y CAS, cambia la garantía de traslado atómico del paquete.
Se elige O2; no se rebajan los criterios de T-05 para obtener verde.

## Decisión

La biblioteca operativa nueva reside en ext4 dentro de un VHDX dedicado:
`data/_storage/studio-data.vhdx`. El archivo físico sigue dentro del
proyecto. Su punto de montaje WSL es una vista virtual del almacenamiento,
con identidad/UUID acreditados; es la única ampliación de la regla de rutas
de ADR-0005. No se añade persistencia en AppData, otra unidad o un volumen
Docker ajeno al proyecto. Código, modelos, herramientas y evaluaciones
conservan sus ubicaciones existentes.

Todos los servicios de producto siguen en Docker; Ollama sigue compartido
en WSL2. El montaje es provisión de plataforma, no un nuevo worker anfitrión.
Server y engines consumidores ven el mismo filesystem; los engines sólo
escriben su subárbol crudo autorizado. El server no recibe SYS_ADMIN,
dispositivos loop ni socket Docker. No se usa loop privilegiado sobre 9p.

La raíz lógica de biblioteca mantiene `data/tmp`, `data/songs` y los paths
relativos de contratos/manifiestos. El montaje puede vivir fuera del árbol
NTFS como vista virtual, pero no representa una segunda copia o fuente de
verdad. Los archivos ext4 se consultan desde Docker/WSL o se exportan de
forma explícita al proyecto; no se promete acceso directo NTFS a las mismas
rutas. Los wrappers del proyecto deben ejecutar las verificaciones sobre
la biblioteca montada, manteniendo los comandos y resultados requeridos.

La provisión comienza con un disco propio nuevo y vacío. No copia, mueve,
formatea ni adopta la biblioteca existente automáticamente. Sólo se opera
con el archivo y disco propios por identidad acreditada; nunca un disco
físico enumerado por posición. Attach/detach requieren el privilegio de
plataforma y no detienen WSL, Docker ni Ollama globalmente.

Startup y Compose deben abortar si falta el montaje, difieren UUID/raíz,
resulta readonly/9p o falla la prueba nativa de NOREPLACE. No deben crear un
directorio vacío como fallback. El publicador conserva paquete cerrado,
manifiesto inmutable, rename de directorio no-clobber, CAS y reconciliación
prepared→renamed→committed; bytes/rename siguen fuera de writer/barrera.

## Recuperación y backup

Un st_dev de una sesión no identifica por sí solo un montaje posterior.
La reconciliación acredita raíz/UUID y propiedad del paquete; no adopta
destinos sólo por nombre o hash. Restaurar una biblioteca exige importar
autoridad y validar assets/BD/manifiestos, no reutilizar leases o procesos.

Se conserva backup lógico coherente de SQLite y assets en un destino
explícito del proyecto. Copiar el VHDX mientras está activo no se considera
backup consistente. El backup de imagen requiere quiesce/flush/detach del
disco propio y verificación posterior. No `wsl --shutdown` ni limpieza de
volúmenes/servicios ajenos.

## Verificación pendiente

Preparación y preflight con TDD, revisión fresca y QA independientes. Prueba
real sobre VHDX persistente: WAV→FFmpeg→rename→assets/ready/song.json,
destinos ajenos vacíos/no vacíos/archivos/enlaces y carreras, crash/cancel,
reconcile y replay sin sobrescritura. Reinicio de contenedores y detach/
reattach propios conservan biblioteca; server/engines comparten la raíz.
Backup/restauración real y verificador de manifiestos sobre dicha raíz.
Tmpfs y tests simulados no acreditan estos gates ni cierran T-05/M1.

La sesión actual comprobó que no tiene token de administrador. Se prepara
la implementación y el procedimiento concreto; no se afirma haber creado,
adjuntado o validado el disco persistente.

Fuentes: [WSL y discos/VHD](https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk)
y [Docker con filesystem Linux](https://docs.docker.com/desktop/features/wsl/best-practices/).
Estas documentan capacidades de plataforma; no prueban nuestro despliegue.
