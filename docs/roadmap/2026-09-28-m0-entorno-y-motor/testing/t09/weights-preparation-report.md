# T-09: preparación de pesos XL fijados

El fetcher canónico terminó exit0, 2026-10-06T05:11:19–05:16:01UTC: `uv run --frozen --no-sync --all-packages python scripts/fetch_models.py --model ace-step-1.5 --include-optional`. [Recibo](weights-preparation-receipt.json).

XL-turbo revisión `d4a0b288b83ebb7e25a8c0b32c573c22e134e8ee`, cuatro shards safetensors: **19.949.340.504 bytes (18,58 GiB)**. Están bajo `models/ace-step-1.5/checkpoints/acestep-v15-xl-turbo/`. El tamaño de archivos no predice VRAM/RAM ni acredita que quepa INT8/offload.

Antes de descargar, se corrigió únicamente el registro `silence_latent.pt` de XL: era metadata y contiene el mismo pickle por SHA que Turbo/SFT/base. Ahora declara pickle y el convertido auditado idéntico, sin modificar revisión/hash original. El auditor produjo un safetensors de un tensor; no se conserva el pickle ni se usa torch.load/pickle.load. Root comparó el JSON con HEAD y comprobó que no hay otro cambio de lock.

El fetcher verifica SHA durante preparación; root cotejó diez archivos finales y sus sellos de tamaño/mtime/SHA contra el lock, sin repetir hashing de20GB. Se conservan bytes/valores del lock tras la reserialización del fetcher. Logs y backup exactos son privados dentro del proyecto.

No se cargó ningún modelo en GPU, no se midieron INT8, inferencia, RTF ni memoria y no se cambia el motor por defecto. Quedan implementación, revisión, QA y ejecución real de la matriz T-09. La estimación de tamaño del proveedor recogida en el diseño no sustituye los bytes fijados en este recibo.
