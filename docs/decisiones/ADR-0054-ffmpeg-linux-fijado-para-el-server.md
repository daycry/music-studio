# ADR-0054 · FFmpeg Linux fijado para el server

- **Estado:** aceptada bajo delegación autónoma; adquisición y pruebas de runtime pendientes.
- **Fecha:** 2026-10-08.
- **Relacionadas:** [ADR-0035](ADR-0035-despliegue-docker-y-ollama-wsl.md), [ADR-0053](ADR-0053-postproceso-cpu-portable-en-el-server.md).

## Decisión

El server Debian usará el build estático `linux64-lgpl` de BtbN, release mensual `autobuild-2026-09-30-13-08`, versión `n9.0.2-17-g2a571b6068`. El archivo fijado tiene 137863452 bytes y SHA-256 `2d41cbea0ca1a15029b638330740f78d6f5aeb062355bf425433fc938705350a`. La API del proveedor y su manifiesto de checksums coinciden; todavía no se han descargado ni ejecutado sus bytes.

Se prefiere el estático al compartido para reducir la configuración de bibliotecas del server. Una construcción propia exigiría fijar también las dependencias y el compilador; el checksum accesible del tarball fuente investigado no está acreditado. La compatibilidad ABI del binario elegido con el contenedor sigue pendiente de prueba.

La [receta fijada](https://raw.githubusercontent.com/BtbN/FFmpeg-Builds/6c9aec5fc9a72ec3abedd1fa84db141fa18cf52b/variants/defaults-lgpl.sh) activa `--enable-version3` y elige `COPYING.LGPLv3`. Se registra **LGPLv3**, sin extender esa conclusión a otros builds existentes. Los flags y la licencia del binario se comprobarán en el contenedor antes de usarlo. La receta tampoco sustituye los avisos de las bibliotecas incluidas.

Los pins Linux viven en un lock separado del Windows existente. La adquisición debe verificar tamaño y SHA antes de extraer, rechazar traversal, enlaces, dispositivos y miembros ambiguos, y publicar únicamente su directorio nuevo. Una carga existente se verifica contra la procedencia original y se conserva ante dudas. `--check` debe verificar archivos, no sólo ejecutar `-buildconf`. La extracción ZIP histórica no se reutiliza para TAR.

## Verificación

La descarga ocurre en una herramienta explícita de preparación, nunca al arrancar el server. El runtime Docker exige comprobar `-version`, `-buildconf`, `-L`, filtros y encoders necesarios; procesar audio real con `audio-post`; y probar cancelación y terminación de FFmpeg en el grupo propio. Se conservan licencias, avisos y procedencia antes de incluirlo en la imagen. No se acredita distribución comercial ni el cierre de T-05 con esta decisión.
