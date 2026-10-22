---
id: GOT-001
tipo: gotcha
area: almacenamiento
estado: propuesta
fecha: 2026-10-09
fuente: docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-tool-metadata.md
---

# FD sobre bind Windows: rename cambia la correspondencia observada

## Síntoma

El `mke2fs` Debian fijado recibe `/proc/self/fd/3` de un archivo propio de64MiB
y devuelve `Device size reported to be zero`. La llamada conserva el FD
heredado, pero el archivo había sido renombrado y su nombre original ocupado
por un testigo de45bytes.

## Causa raíz

Seis controles sobre la misma imagen/herramientas aislaron el bind Windows9p:
sin rename, fstat/getsize ven64MiB; rename-only produce ENOENT en fstat/reopen;
rename+replacement hace que fstat/reopen vean45bytes y getsize calcule cero
bloques. El pread del FD original y el del reopen no observan necesariamente
los mismos bytes. Los controles tmpfs conservan64MiB después de ambas
operaciones. Conservar únicamente dev/ino no acredita esa correspondencia.

La causa está probada para este Docker Desktop/WSL y este bind. No se afirma
que todos los filesystems9p ni todas las operaciones con FDs tengan ese resultado.

## Qué hacer en su lugar

Para la provisión offline prevista, conservar guardianes Windows de archivo
y ancestros sin FILE_SHARE_DELETE, con FILE_ID_INFO y comprobaciones de
reparse/hardlinks, durante las operaciones Linux sobre los mismos FDs.
El prototipo real bloqueó siete intentos Windows y siete Linux de rename/delete;
el formato ext4, comprobación sin reparación, creación VHDX, convert-n e info/
compare terminaron0. Hashes Windows/Linux finales coinciden.

No pasar bloques explícitos para ocultar el tamaño observado ni cambiar a
una ruta por nombre como fallback. El prototipo sólo acredita esa mitigación
y conversión privada: executor, promoción por handle, crash, montaje y
persistencia conservan puertas propias. La limpieza Linux de probes tiene
hallazgos independientes y esta entrada no los acepta.

## Evidencia

[Informe público](../../roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-tool-metadata.md)
y [diseño](../../roadmap/2026-09-28-m1-mvp-estudio/storage-execution-design.md).
Recibos privados reproducibles en el proyecto:
`t05-storage-tool-fd-debug1/phase3-cause.json`,
`t05-storage-windows-custody-probe1/probe-junit.xml` (27PASS),
`t05-storage-tool-root1/root-fd-cause-verification.json` y
`root-guardian-verification.json` (43artefactos, nueve comandos reapados).
