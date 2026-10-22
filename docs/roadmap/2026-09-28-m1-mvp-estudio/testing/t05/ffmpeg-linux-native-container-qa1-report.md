> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# QA independiente FFmpeg Linux

**PASS técnico acotado** en Debian 12 Bookworm/amd64, imagen local exacta `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`. Python del contenedor 3.12.14 (main, Sep 19 2026, 01:05:48) [GCC 12.2.0]. El server Dockerfile usa esta base; su imagen completa no se construyó ni ejecutó.

| Sonda real | Resultado |
|---|---|
| Script global intacto `--check`, ROOT natural `/studio`, lock actual | exit 0 |
| FFmpeg `-version`, `-buildconf`, `-L`; ffprobe `-version` | cuatro exit 0 |
| WAV/FLAC/MP3 sintéticos: 1 s, 48 kHz, estéreo, ffprobe y decode finito | nueve exit 0 |
| Baseline privada, dos binarios oficiales copiados sin alterar bytes | exit 0 |
| ffmpeg sin X / restaurado 0755 | exit 2 esperado / exit 0 |
| ffprobe sin X / restaurado 0755 | exit 2 esperado / exit 0 |
| `_publish(stage,dest)` real, renameat2 Linux, destino ausente | publicado |
| `_publish` destino existente | EEXIST; ambos testigos y fuente preservados |

Los 19 comandos nativos conservan argv, UTC, exit y stdout/stderr. Los dos calls nativos de `_publish` conservan identidad del módulo, parámetros, UTC, errno y testigos. No hubo monkeypatch de plataforma/pin/stat/API ni testdouble. Módulo copiado SHA 02f11245ee8609341c3f9ebc2ea8dde350e701a22442eac8b21dbb2b6d425401.

Flags: `--enable-version3` presente; `--enable-gpl` y `--enable-nonfree` ausentes. El binario autodeclara LGPL versión 3 o posterior; LICENSE.txt contiene LGPLv3. Se conserva configuración completa y avisos disponibles. La completitud de avisos de dependencias y la redistribución legal no quedan certificadas.

**Discrepancia documentada:** 69 archivos reales = 66 declarados en procedencia + `.archive.tar.xz`, `.provenance.json`, `.owner`. El recuento 70 del prompt/aceptación anterior no se confirmó. Inventarios completos antes/después coinciden; el archive tiene 137863452 bytes y SHA `2d41cbea0ca1a15029b638330740f78d6f5aeb062355bf425433fc938705350a`.

Intento inicial detenido antes de Docker por esperar 70. Primera ejecución real pasó global/ABI/licencia/codecs; falló sólo la fixture privada: directorios root creados por Docker para el bind anidado impedían escritura UID10001. Se reparó la configuración privada: payload y lock readonly con overlay tmpfs sólo para los dos binarios; ffplay readonly, nunca ejecutado. Se reutilizaron los éxitos anteriores sin repetir codecs. Tmpfs 384+16=400 MiB, límite de memoria 1 GiB, CPU2/PIDs64, usuario10001, red none, readonly, cap-drop ALL, no-new-privileges, sin GPU.

Ambos contenedores fueron esperados hasta exit real (1 de fixture / 0 de sondas), inspeccionados terminales y eliminados sólo por sus IDs exactos y labels propios. El parser inicial escribió ownGone=false por comparar mayúsculas; la auditoría de sus originales `rm exit0`, ID exacto y `inspect error: no such object` + `[]` acredita eliminación. Originales preservados sin reescritura en native-attempt1.

14 fuentes con copias exactas y 7 protegidos permanecen intactos. Ownership producto `[]`; salida sólo en esta fase privada. TDD n/a: QA de código existente sin cambios; las sondas negativas no son RED nuevo. Cobertura n/a: no cambios de producción ni cifra nueva atribuida. Métricas modelo/tokens/EUR/horasIA NULL.

No acredita acquire completo, extracción/publicación/cleanup de lock, audio-post/worker/takes/song/derechos/calidad musical, integración de la imagen server, otros Linux, T05/M1/E2E/GPU. No se escribió ledger/docs/licencias/Git/aceptación/meter.

Evidencia: receipt.json, actor-command-accounting.json, native-command-accounting.json, native-attempt1/native-command-accounting.json, native-publish-events.json, mode-transitions.json, smoke-results.json, sources-before/after.json, payload-before/after.json, private-payload-before-chmod/after.json, container-created/terminal.json, cleanup-evidence-audit.json y noncli-inventory.json.
