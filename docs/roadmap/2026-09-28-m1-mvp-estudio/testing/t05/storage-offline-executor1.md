# Executor offline T-05 — raw ext4 y VHDX temporal

Fecha: 2026-10-10

Se implementó `scripts/storage_offline.py` y el contrato `studio_storage_guard.receipt.StorageReceipt`. El executor:

- reserva una carpeta única bajo `.cache/dev-cycle/storage-<operation_id>`;
- rechaza una reserva o un `data/_storage/studio-data.vhdx` existente;
- ejecuta `mke2fs`, `e2fsck -fn`, `qemu-img create`, `qemu-img convert -n` y `qemu-img info` dentro del contenedor de herramientas fijado;
- verifica SHA-256/tamaño del raw y del VHDX;
- escribe un recibo monotónico hasta `vhdx_verified`;
- conserva la reserva si una herramienta falla para impedir adopción o limpieza ambigua.

TDD y verificación:

- RED: `tests/test_storage_offline.py` no podía importar el executor inexistente.
- GREEN unitario: **8 passed**.
- Recibo de fases: `packages/storage-guard/tests/test_receipt.py` **3 passed**.
- Regresión del paquete storage-guard: **93 passed, 42 skipped**.
- Ruff de los cuatro ficheros nuevos: limpio.
- Ejecución real con `music-studio-storage-tools-t05-runtime1:private`, 64 MiB, ext4 UUID `12345678-1234-5678-1234-567812345678`: `mke2fs`, `e2fsck`, conversión VHDX e `info` terminaron con exit 0. Recibo en `.cache/dev-cycle/storage-01ARZ3NDEKTSV4RRFFQ69G5FAV/receipt.json`; raw 64 MiB y VHDX 75497472 bytes, SHA-256 `44b843...803b` y `86ed0c...9db7`.

La promoción por handle Windows ya está verificada y el recibo está en `published`; no se ha ejecutado attach, mount ni validación ext4 persistente. Por tanto T-05/T-15 siguen abiertos.



## Publicación custodiada — 2026-10-10

- TDD de `scripts/storage_publish.py`: RED por módulo ausente; GREEN **3/3** con fuente verificada, destino existente preservado y fuente manipulada rechazada.
- Custodia Windows + publicación: `tests/test_storage_publish.py` y `tests/test_storage_windows.py` **17 passed**; Ruff limpio.
- Ejecución real: el VHDX temporal se copió mediante un archivo creado bajo `WindowsCustody`, se selló por SHA-256 y se promovió con `ReplaceIfExists=FALSE`. El recibo quedó en `published` con identidad `VolumeSerialNumber+FileId`.
- Verificación Docker del destino final: `qemu-img info` sin red, solo lectura, `dirty-flag=false`.
- Pendiente: attach/mount WSL, UUID/mountinfo/NOREPLACE en el volumen montado, wiring de Compose y E2E de publicación persistente.


## Operador WSL attach/mount — 2026-10-10

- Se añadió `scripts/storage_attach.py`: valida el recibo `published`, exige el VHDX exacto, ejecuta `wsl.exe --mount <vhdx> --vhd --bare`, compara `lsblk` antes/después y sólo acepta un bloque ext4 nuevo con el UUID del recibo.
- Valida `findmnt` (`ext4`, raíz `/`, `rw`) y `blkid`; ante cualquier fallo intenta `umount` privado y `wsl.exe --unmount <vhdx>`. Nunca detiene WSL, Docker u Ollama globalmente.
- RED por módulo ausente; GREEN focal **6/6**. Suite T-05 de publicación, attach y custodia Windows: **23 passed**; Ruff limpio.
- En la sesión actual, `--execute` devuelve `NEEDS_ADMIN` sin efectos; el modo de plan deja la secuencia completa lista. El montaje real, `attached`/`validated`, wiring de Compose y E2E persistente siguen pendientes de una sesión elevada.


## Override Compose y UUID — 2026-10-10

- `docker-compose.storage.yml` exige `STUDIO_STORAGE_UUID` en server, engine-mock, engine-analysis y engine-acestep; la raíz sigue usando `create_host_path: false`.
- TDD: RED por ausencia del contrato; GREEN **1/1**. `docker compose --profile studio -f docker-compose.yml -f docker-compose.storage.yml config -q` termina con exit 0 usando raíz y UUID de prueba.
- El override no arranca servicios ni convierte un bind en evidencia de montaje; sigue condicionado al operador WSL y al preflight nativo.
