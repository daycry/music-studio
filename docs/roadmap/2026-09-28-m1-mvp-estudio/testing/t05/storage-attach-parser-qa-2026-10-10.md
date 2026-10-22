# T-05: corrección del protocolo lsblk — revisión y QA CPU

La corrección usa la salida JSON real de `lsblk`, incluidos campos nulos, swap y dispositivos hijos. Rechaza estructuras inválidas, entradas duplicadas y UUID ambiguos. Conserva la comparación antes/después y la parada `NEEDS_ADMIN` sin efectos.

TDD: los dos RED de parser y comando constan en el ledger y preceden a la implementación. El delta está limitado a `scripts/storage_attach.py` y `tests/test_storage_attach.py`. La comprobación oficial de alcance del componente termina con exit 0: dos archivos dentro, ninguno fuera y sin exclusiones. Esta comprobación no atribuye un alcance limpio al checkout compartido completo.

Revisión independiente A/B, intento 1: 0 Critical, 0 Important y 0 Minor. Ambas lentes repiten 53 pruebas y comprueban que selección de dispositivo, protección administrativa y ejecución permanecen intactas fuera del cambio del protocolo.

QA independiente: funcional **53/53**, cobertura **53/53**, ambos exit 0. Cobertura oficial de todo el módulo modificado **191/210 = 90,95 %**, sin exclusiones. Identidad de fuentes antes/después confirmada. El orquestador verifica **27 artefactos** del inventario y **7 hashes** de fuentes, preimágenes y evidencia, con exit 0.

Evidencia local: `.cache/dev-cycle/m1/storage-attach-parser-20261010/worker/`, `component-scope-official.json`, `qa/receipt.json`, `qa/artifact-inventory.json` y `root-verification.json`. Las rutas de caché contienen recibos privados y no se publican como datos del repositorio.

**Límite:** no se ejecuta attach, montaje WSL, provisión POSIX, Docker, GPU ni E2E persistente. No se declara un gate de UI a partir de estos tests de CLI. T-05 y M1 siguen abiertos.
