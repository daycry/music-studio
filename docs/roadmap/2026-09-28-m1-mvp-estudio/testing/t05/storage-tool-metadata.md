# Herramientas fijadas para provisión offline

Fecha: 2026-10-09. Alcance: metadatos y autorización de adquisición local.
No acredita binarios instalados, conversión por FD, custodia entre plataformas,
VHDX montado ni persistencia de T-05.

El diseño elegido prepara ext4 en un archivo nuevo propio y lo convierte a
VHDX antes de adjuntarlo por su ruta exacta. Se mantiene
[ADR-0069](../../../../decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md).
Las herramientas se fijan en
[storage-linux.lock.json](../../../../../tools/storage-linux.lock.json), fuera
del Python del anfitrión y sin instalación global de paquetes Debian.

| Componente | Versión Debian fijada | SHA-256 del archivo oficial |
|---|---|---|
| qemu-utils, sólo qemu-img | `1:7.2+dfsg-7+deb12u18+b3` | `53adfeadecfacde490131beda1c0f2ddedba2f94ed2e44867eac061af2fbfe32` |
| e2fsprogs | `1.47.0-2+b2` | `fedd424691c08ef0739729026be298e7be8236337bf8e031b3c7ec66794e6fc2` |

La base propuesta es Python 3.12.14 slim Bookworm amd64 por digest. Los30paquetes
y sus versiones, URL, tamaño y hash están en el lock. Es el cierre declarativo
de Depends/Pre-Depends, no un análisis de todos los ELF ni una prueba ABI.
Recomendaciones como qemu-block-extra no entran automáticamente: los formatos
raw/VHDX deben comprobarse en el ejecutable real.

## Evidencia revisada por Root

Investigación privada congelada en `t05-storage-tool-candidates1`:90artefactos
verificados por tamaño/hash; seis índices comprimidos/descomprimidos concuerdan
con los SHA/tamaños de InRelease; los30pins concuerdan con las estrofas originales.
Las68restricciones declarativas se informan satisfechas. Los tres logs gpgv
finales contienen GOODSIG/VALIDSIG y terminal0. Las claves proceden del HTTPS
oficial Debian, sin canal independiente de confianza.

Verificación Root: `uv run --no-sync python -B .cache/dev-cycle/verify-storage-tool-candidate-root.py`, sesión6703 terminal0.
Recibo privado `t05-storage-tool-root1/root-metadata-verification.json`.
SHA del lock resultante:
`96871d907f50d78583287a1f1f7464bc46a604418d8f48929b85704450e8d4f5`.
El JSON candidato originalmente cp1252 se reparó a UTF8; la comparación
semántica contra los bytes originales preservados fue igual.

## Puertas antes de ejecución

Cada DEB se compara con tamaño y SHA antes de extraerse dentro del bundle
privado del proyecto. Se conservan copyrights reales y textos referidos; no
se ejecutan scripts de instalación ni servicios del paquete. Las filas de
[licencias](../../../../legal/licencias.md) registran QEMU/e2fsprogs y el bundle
por separado. No se atribuye una licencia única a sus bibliotecas.

Se recuperaron21copyrights fuente exactos de22. El endpoint de PCRE2 security
`10.42-1+deb12u2` devolvió404. El aviso de su predecessor es sólo suplementario:
el aviso del DEB exacto verificado debe extraerse antes de ejecutar herramientas.
Las firmas de los DSC por claves de mantenedores no fueron verificadas.
Las URL de pool pueden desaparecer; sólo se aceptan bytes que coincidan con el pin.

La fase siguiente verifica base/sysroot, loader y DT_NEEDED, ejecutables,
configuración ext4 explícita y operaciones reales sobre FDs propios. QEMU7.2
no hereda una garantía inferida del código QEMU10. No hay fallback a rutas
mutables si falla el FD, ni uso de `-U`, `--salvage` o `--target-is-zero`.

Las pruebas offline sobre archivos propios no sustituyen la custodia Windows,
promoción sin reemplazo, attach del VHDX, startup dentro de cada consumidor,
replay persistente, reinicio ni backup/restauración.

## Adquisición y primer diagnóstico real

Root verificó los30DEBs adquiridos:11.136.896bytes, tamaños y hashes exactos
contra el lock. El copyright de PCRE2 se obtuvo del miembro
`./usr/share/doc/libpcre2-8-0/copyright` del DEB verificado, SHA
`030511beb4d9d620ad09914c369c36ec0528dcf301d1923cc643c948ee7c6a38`.
Coincidir en bytes con el predecessor no fue su prueba de origen: la autoridad
es ahora el archivo exacto fijado. El gap de adquisición de ese aviso se cierra;
el fallo del endpoint de metadatos anterior se conserva como histórico.

El sysroot permanece físicamente en el proyecto mediante `sysroot.tar`
(38.715.392bytes; SHA
`fb9e6300275973ced19bd1fd81d916b18351d2e7d9151a5af78e11a8ff4d05d3`),
sin materializar enlaces Linux en Windows. Root contrastó579sellos de archivos
y enlaces del TAR y30copyrights, además del inventario congelado139artefactos.
La extracción informa326ELFs y dependencias privadas resolubles; ese inventario
no demuestra qué biblioteca se mapeó efectivamente en cada proceso.

El diagnóstico ejecutó cinco consultas de versión y ayuda de QEMU por su
loader privado: QEMU7.2.22 empaquetado por Debian y e2fsprogs1.47.0. La ayuda
incluye raw/VHDX. Los seis comandos terminaron0. El séptimo, `mke2fs` por
`/proc/self/fd/3` con FD heredado de un archivo propio de64MiB, terminó1:
`Device size reported to be zero`. Esto **no** prueba conversión ni formato ext4.
No se ejecutaron los comandos posteriores de verificación/conversión ni se
introdujo un fallback a nombres de archivo.

JUnit del diagnóstico: ocho assertions pasan y una falla. Los siete hijos
terminaron y se reaparon; cuatro fixtures propias se limpiaron por identidad
y los FDs se cerraron. El contenedor propio terminó1 y se eliminó. Root
comprobó Runtime=runc, ausencia de devices/DeviceRequests/privilegios, red none,
rootfs RO, usuario1000 y CapDropALL. La exportación usó otro contenedor propio
sin arrancarlo, también eliminado. No hay montaje ni GPU.

Recibos Root: `t05-storage-tool-root1/root-acquisition-verification.json` y
`root-failed-runtime-verification.json`; comandos de verificación terminaron0.
Ese cero valida la evidencia del **fallo**, no la convierte en éxito de runtime.
El diagnóstico congelado `t05-storage-tool-runtime1` permanece intacto.
La fase nueva `t05-storage-tool-fd-debug1` sigue el método de causa raíz antes
de decidir otra invocación sobre los mismos FDs propios.

## Mitigación por guardianes Windows: diagnóstico privado aceptado

El nuevo diagnóstico mantuvo diez handles Windows de archivos/ancestros sin
FILE_SHARE_DELETE mientras el hijo utilizaba los mismos FDs3/4/5. Siete
rename/delete Windows devolvieron ERROR32 y siete Linux EACCES13. Identidades,
tamaños y contenido antes de formato no cambiaron. Root verificó43artefactos,
27assertions PASS y nueve comandos reales reapados exit0: mke2fs por FD,
UUID, debugfs, e2fsck-f-n, VHDX válido, convert-n, info y compare.

Raw64MiB y VHDX lógico64MiB (75.497.472bytes físicos) produjeron hashes
Windows/Linux iguales. El testigo quedó intacto. Después se cerraron FDs/
handles y se eliminaron el contenedor propio y tres fixtures propias.
Recibo `t05-storage-tool-root1/root-guardian-verification.json`.

Este éxito sólo acepta la mitigación del prototipo privado de provisión.
Executor de producto, promoción por handle, recuperación, attach y montaje
persistente siguen pendientes. La limpieza de probes Linux tiene revisión
independiente con gaps; [ADR-0071](../../../../decisiones/ADR-0071-probes-de-almacenamiento-en-dominio-aislado.md)
define su dominio aislado y no se valida con los guardianes Windows de este
diagnóstico. [GOT-001](../../../../knowledge/gotchas/GOT-001-fd-9p-tras-rename.md)
registra la causa como propuesta, sin promoción implícita.
