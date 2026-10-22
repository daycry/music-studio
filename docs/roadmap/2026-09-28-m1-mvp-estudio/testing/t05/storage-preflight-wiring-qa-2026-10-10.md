# T-05: conexión del preflight Linux con IPC — revisión y QA CPU

El preflight de producción conecta el cliente IPC fresco y el probe anónimo con el descriptor de la ruta original. Revalida la lease antes, entre y después de ambas operaciones. Library RO no escribe ni realiza IPC. Raw usa la raíz original de library como control; cualquier fallo cierra ambas leases.

El delta se limita a `packages/storage-guard/studio_storage_guard/preflight.py` y `packages/storage-guard/tests/test_preflight.py`. El RED previo `STORAGE_ROOT_INVALID` y el GREEN constan en el ledger. Scope oficial del componente: exit 0, dos archivos dentro, ninguno fuera ni excluido. No es un gate del checkout compartido completo.

Revisión A/B, intento 1: 0 Critical, 0 Important y 0 Minor. A repite 16 tests de la ruta default; B repite los 42 tests de preflight. Ambas verifican los hashes y el cierre ante errores.

QA independiente funcional y cobertura: **109 pasadas, 42 omitidas por Linux, cero fallos**, exit 0. Cobertura oficial WHOLE del módulo modificado **180/195 = 92,31 %**, sin exclusiones; supera el 80 %. La cobertura de todo el paquete **504/803 = 62,76 %** es informativa y no supera el 80 %. Ruff y formato exit 0; ledger-lint sin incoherencias y con un aviso de codificación preexistente.

Root verifica **23 artefactos** del inventario y los **2 hashes** actuales, antes/después, con exit 0. Se conservan los incidentes del wrapper de shell y del parser JSON de PowerShell: ocurrieron tras las comprobaciones y no se omiten ni se presentan como fallos de producto. No se repitieron las pruebas para ocultarlos.

Evidencia local: `.cache/dev-cycle/m1/storage-preflight-wiring-20261010/worker/`, `component-scope-official.json`, `qa/receipt.json`, `qa/inventory-sha256.json` y `root-verification.json`.

**Límite:** las seams de Windows prueban el wiring CPU. No prueban SCM_RIGHTS Linux, permisos efectivos, namespaces Docker, ext4/VHDX ni montaje persistente. No se ejecuta UI, GPU o un gate de Playwright. Componente CPU aceptado; T-05 y M1 permanecen abiertos.
