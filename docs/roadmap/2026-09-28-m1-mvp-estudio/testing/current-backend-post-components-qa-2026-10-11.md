# Validación actual del backend CPU — 11 de octubre de 2026

**Aceptado por ROOT en el alcance funcional CPU. M1 continúa NO-VERDE; T-05 y T-15 permanecen abiertos.** Esta ejecución comprueba las fuentes posteriores a los componentes corregidos. No modifica ni sustituye la evidencia histórica de los fallos.

| Grupo independiente | PASS | SKIP | FAIL | ERROR | Salida pytest |
|---|---:|---:|---:|---:|---:|
| Suite principal | 2135 | 18 | 0 | 0 | 0 |
| Custodia nativa Linux | 52 | 0 | 0 | 0 | 0 |
| IPC y credenciales | 90 | 0 | 0 | 0 | 0 |
| Credenciales de custodia | 21 | 0 | 0 | 0 | 0 |
| Total sin duplicados | **2298** | **18** | **0** | **0** | **0** |

Los 2316 casos JUnit son distintos. La colección y ejecución de principal y custodia nativa coinciden exactamente. La suite principal ejecutó pytest entre 08:01:31 y 08:22:32 UTC; la preparación anterior no se presenta como tiempo de ejecución.

## Verificación independiente

ROOT verificó 53.132 archivos regulares, 3.332.196.132 bytes, los hashes de 1770 fuentes actuales y 1768 del snapshot inicial, 2889 registros de procedencia de imports, cuatro archivos TAR y sus JUnit exactos. Los archivos del código y los tests permanecieron intactos; las diferencias documentales de ROOT están registradas.

El sello privado es `backend-post-components-qa-20261011/artifact-inventory.json`, SHA-256 `b2b092353f6f46b088e4330a0176336f321b34a652b0eae9ecb6c666790cb6e5`. El recibo de ROOT está en `.cache/dev-cycle/m1/backend-post-components-root-20261011/verification-root.receipt.json`. Todos los TAR finales se generaron después de finalizar pytest, se copiaron y verificaron antes de detener sus contenedores. Los cuatro procesos propios están detenidos, PID 0; los originales quedan conservados para análisis.

La imagen CPU utilizada es `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`. Principal y custodia nativa ejecutan como UID/GID 10001, sin red, con raíz y fuentes de solo lectura, capacidades retiradas y `no-new-privileges`. El padre de los fixtures de credenciales necesita UID 0 y cinco capacidades limitadas para preparar sus hijos; los hijos comprueban capacidades efectivas, permitidas, heredables y ambientales vacías. Esto no acredita un server de producto privilegiado. Las carpetas temporales son fixtures; no acreditan el almacenamiento ext4 persistente de la aplicación.

Principal y custodia nativa incluyen imports por archivo y SHA reales. Los grupos de credenciales sólo acreditan sellos anteriores al import, rutas de cobertura y procedencia inferida del arnés y la configuración. No se afirma haber capturado retrospectivamente sus `sys.modules` ni el directorio actual de cada hijo.

## Cobertura y comparación histórica

Hay 80 archivos completos medidos con cobertura oficial sin exclusiones; ocho quedan por debajo del 80 %. No se declara que todo el backend cumpla ese umbral.

| Componente afectado o ámbito audio completo | Cobertura oficial |
|---|---:|
| `helper.py`, grupo IPC separado con ramas | 96,03 % |
| `custody_linux.py` | 88,32 % |
| `custody_linux_supervisor.py` | 80,55 % |
| `pipeline.py` | 96,32 % |
| `manifest.py`, ámbito audio completo | 84,31 % |
| `resolver.py` | 94,39 % |

Las bases de cobertura de líneas se combinan con la herramienta oficial. La medición IPC con ramas se conserva separada; no se fabrica una combinación entre formatos. El helper no se ejecuta en el grupo combinado de líneas: su cero en ese grupo no reemplaza la medición real del IPC.

ROOT cotejó los 81 nodos fallidos del JUnit histórico original, SHA-256 `c32058acc6a55e0a39fa2869908a1539917e2df7b5ed86110c0fe314c613c22f`, contra los mismos nombres y parametrizaciones actuales: **77 PASS, 4 SKIP, ninguno ausente**. Esto no convierte 81 fallos de preparación o plataforma en 81 bugs corregidos. Los originales rojos permanecen intactos.

## Diagnósticos conservados y límites

Las preparaciones fallidas por rutas de fixtures, pérdida de temporales y captura prematura se conservan y no se cuentan como ejecuciones aceptadas. El replay nativo de 52 casos se justificó porque el primer archivo capturaba un estado incompleto. Se corrigió únicamente el arnés privado; no se relajaron tests ni producto. El exit 137 del proceso inactivo de un contenedor retirado no es un fallo del pytest que ya había terminado.

FFmpeg se ejecutó realmente y sus bytes y versión se verificaron. El hash del archivo de descarga se cotejó con su recibo y lock, sin atribuir a esta QA un nuevo hash de todos sus bytes.

Quedan pendientes almacenamiento persistente real, controller durable, E2E de publicación y recuperación, Range, restauración de biblioteca, validación de UI y las comprobaciones manuales. El módulo de custodia exclusivo de Windows no se ejecutó en esta suite Linux. No hay aceptación integral de M1, cierre de tareas, QA visual ficticia ni cambios de Git. El medidor vigente de ROOT es `m1/lote-u2a-qa-backend-accept`; tokens, euros y horas reales no disponibles quedan `null`.
