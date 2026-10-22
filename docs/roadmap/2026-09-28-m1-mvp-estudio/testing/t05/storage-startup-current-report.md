# T-05 - gate de arranque persistente

Fecha: 2026-10-10

`test_storage_startup.py`, `test_storage_preflight.py` y `test_storage_compose.py`: **31 passed en 0,88 s**. La prueba confirma que el startup falla cerrado si no existe un mount ext4/UUID acreditado y que Compose no crea una carpeta vacia como sustituto. El attach WSL nativo y el E2E persistente siguen pendientes.
