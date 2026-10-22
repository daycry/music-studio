# T-05: adquisicion y runtime privado de herramientas de almacenamiento

Fecha: 2026-10-10

Se implemento `scripts/fetch_storage_linux.py` para adquirir un sysroot
privado dentro del checkout. El ejecutor:

- valida el lock `tools/storage-linux.lock.json` y cada DEB por tamano y SHA-256;
- acepta solo fuentes locales dentro del proyecto o URLs Debian fijadas;
- rechaza rutas TAR inseguras, dispositivos, FIFO, colisiones y destinos existentes;
- materializa enlaces y hardlinks dentro del sysroot sin crear enlaces Windows;
- publica por una operacion sin reemplazo y conserva un `.provenance.json` verificable;
- no instala paquetes, no inicia servicios y no monta discos.

## Evidencia

TDD del helper: `tests/test_fetch_storage_linux.py` -> **6 passed**.
`ruff check` y `ruff format --check` del helper y sus pruebas -> **verdes**.

La importacion de los 30 DEB ya adquiridos en
`tools/storage-linux/debian-bookworm-amd64/bundle-2026-10-09/archives` se
ejecuto en el root aislado `.cache/dev-cycle/m1/t05-storage-acq5`:

```text
storage Linux verificado: .cache/dev-cycle/m1/t05-storage-acq5/...
```

La comprobacion posterior con `--check` paso. El sysroot contiene
`usr/bin/qemu-img` y `sbin/mke2fs`.

La implementacion tambien exige y registra el `copyright` de cada paquete en
la procedencia. La repeticion final en `t05-storage-acq6` paso importacion y
`--check` con esa barrera adicional.

En un contenedor Bookworm fijado, sin red, sin dispositivos y con el sysroot
en solo lectura:

```text
qemu-img version 7.2.22 (Debian 1:7.2+dfsg-7+deb12u18+b3)
mke2fs 1.47.0 (5-Feb-2023)
```

La prueba funcional aislada creo un raw ext4 de 64 MiB con UUID explicito,
paso `e2fsck -fn`, lo convirtio a VHDX y `qemu-img info --output=json` devolvio
`format=vhdx`, `virtual-size=67108864` y `dirty-flag=false`.

## Limites

La ejecucion usa un root de prueba porque el destino oficial existente se
conserva por politica de no reemplazo. Todavia no acredita la promocion por
handle Windows, el traspaso de FD al helper, attach/detach WSL, el mount ext4
de los consumidores ni el recorrido persistente de T-05/T-15. Por tanto no
cierra esas tareas ni M1; deja disponible la siguiente pieza reproducible del
executor.
