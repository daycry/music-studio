# T-05: provisión de dominios y despliegue del helper

El provisionador prepara los dominios de datos, temporales, probes y control con credenciales y permisos distintos. Comprueba montaje ext4, UUID, ancestros y ACL antes de crear por descriptor; publica los permisos de la raíz al final. Un fallo conserva los residuos y bloquea su adopción posterior. El helper Docker usa Python fijado y stdlib, UID 19000:GID 10001; los consumidores usan UID 10001:GID 10001.

El delta revisado comprende `provision.py`, `test_provision.py`, `apps/storage-guard/Dockerfile`, `docker-compose.storage.yml` y `test_storage_guard_deployment.py`. Scope oficial del componente: exit 0, cinco archivos dentro, ninguno fuera ni excluido. La revisión A/B/C, intento 1, termina sin hallazgos Critical, Important o Minor. No acredita el checkout compartido completo.

QA independiente: **176 pasadas, 42 omitidas por requerir Linux, cero fallos o errores**, tanto en ejecución funcional como con cobertura. Cobertura WHOLE de `provision.py`: **162/171 = 94,74 %**, sin exclusiones. La cobertura del paquete completo, **68,38 %**, es informativa y no supera el gate general del 80 %. Ruff y formato exit 0. Ledger sin incoherencias, con aviso UTF-8 preexistente; comprobación del plan sin referencias rotas y aviso T-00.

El orquestador coteja 20 artefactos del inventario, cinco fuentes actuales y siete terminales con exit 0. Comprueba también ambos JUnit y los datos oficiales de cobertura. Recibos privados en `.cache/dev-cycle/m1/storage-domain-deployment-review1-20261010/qa/` y `root-verification.json`.

## Verificación real de Docker

La resolución de Compose fusionada pasa con UUID y raíz de ejemplo: cinco servicios, credenciales, capacidades eliminadas, `no-new-privileges`, dependencias y mounts esperados. Esos valores de ejemplo no acreditan un montaje autorizado.

`docker build --pull=false --network=none -f apps/storage-guard/Dockerfile -t music-studio/storage-guard:m1-t05 .` termina exit 0. La imagen producida es `sha256:1c18c0ef8ed31d824452f8f3d449f93700c1f26fabd90c4ca0c7c69190df719d`. La resolución de metadatos del registro durante el build consta en la salida; `--network=none` no garantiza build sin acceso al registro.

La ejecución por ese ID, sin red, con raíz de contenedor de solo lectura, `--cap-drop=ALL` y `--security-opt=no-new-privileges`, verifica las credenciales reales/salvadas/efectivas **19000:10001**, grupo suplementario únicamente 10001, capacidades efectivas y bounding **cero**, `NoNewPrivs=1` y Python **3.12.14**. Importa helper y provisionador dentro del contenedor. El arranque por defecto sin UUID y con UUID inválido termina exit 1, como corresponde; no se simula un almacenamiento válido.

Los tres contenedores propios terminan y su ausencia se verifica. Recibos, comandos y salidas en `runtime/receipt.json` y `runtime/runs.json` del mismo directorio privado. No se carga ningún modelo GPU ni se toca Ollama.

## Límites de aceptación

La evidencia permite aceptar el componente CPU y las credenciales del contenedor. Quedan montaje ext4/VHDX, primitivas Linux/ACL originales, IPC positivo sobre ese montaje, permisos efectivos de consumidores, binding/custodia del controlador, validación/desmontaje y manuales. UUID y montaje fresco por sí solos no prueban vinculación con el VHDX autorizado. **T-05 y M1 permanecen abiertos.**
