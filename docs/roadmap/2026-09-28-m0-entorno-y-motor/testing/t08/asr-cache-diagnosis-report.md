# T-08 — causa ASR: caché Triton sin permisos

2026-10-06. Una ejecución GPU diagnóstica sobre la imagen original306e3b0 y el fixture privado30s. Previamente revisión A+B+D y QA independiente40checks CPU, fuentes2SHA congeladas. No se cambiaron loaders/algoritmos. Preflight nuevo1314MiB/Ollama vacío/engine8101 idle y descargado.

## Evidencia real

Job01EF0BEC81B7364E2A95A5FFF5: cargaQwen completada, adapter.generate→backend.run→Qwen transcribe→Transformers generate→RoPE→torch operación bmm→Triton inicialización del driver→compilación/cache→PermissionError errno13 al crear `/studio/.triton`. Se captura el mismo error en backend.run y adapter.generate; no llega a cargar el alineador. PadrePID1 sinTorch; hijoPID11. Terminal único error/INTERNAL, runnerexit2, wrapper hostexit1; no se declara testpasado.

Duración103,5s; sin timeout del host. Descarga del hijo y borrado del TMPfallido confirmados por runner. Docker--rm retiró el contenedor propio; baseline posterior1314MiB/Ollama vacío. Se conserva el servicio8101. No se midieron pico/spill y no se afirma OOM ni precisión ASR. Logs y traceback completos permanecen privados, fueraTMP, congelados en recibo.

## Causa y aislamiento CPU

En la misma imagen, usuario engine/UID10001 tiene home `/studio`; no hay TRITON_CACHE_DIR definido. Dockerfile hace escribible `/studio/.cache`, pero `/studio` sigue root. FileCacheManager real de Triton reproduce PermissionError13 `/studio/.triton` en CPU, sinGPU/modelos. Contrafactual soloENV `TRITON_CACHE_DIR=/studio/.cache/triton-probe` permite crear/escribir/leer un archivo de caché. No altera algoritmos ni permisos amplios ni usa root.

Primera invocación del probe CPU falló por quotingPowerShell antes de ejecutar código; se repitió como archivo montadoRO y terminóexit0. Esto es aislamiento causal, no un RED de producto ni una aprobación musical. El helper de publicaciónQA escribió documentos/ledger y después falló por sys.path al importar generate; recovery solo completó preflight y comprobó identidad de lo ya publicado, sin duplicar escritos.

## Corrección siguiente

Implementer fresco con TDD: regresión real del FileCacheManager con UIDruntime y configuraciónpor defecto de imagen; fijar directorio de caché Triton dentro de `/studio/.cache` con permisos engine, sin modificar modelos/loaders/guardas ni ejecucióncomo root. README y tagfinal nuevo de análisis actualizados, manteniendo correcciónCLAP. Después revisión A+B y lentes condicionales/QACPU/image freeze y repetir solo ASR diagnóstica; la alineación secuencial/precisión y T08CA siguen pendientes. No repetir las cuatro pruebasGPU a ciegas ni cerrarM0.
