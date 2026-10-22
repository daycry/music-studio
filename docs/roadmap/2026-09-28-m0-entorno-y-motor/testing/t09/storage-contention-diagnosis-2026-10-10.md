# T-09 — Reproducción del timeout durante copia de pesos

La preparación de pesos en Docker reproduce el `worker_deadline` del observador sin cargar modelos ni generar audio. El timeout no basta para atribuir el fallo a WDDM o Edge: los resultados pueden estar calculados mientras el registro de progreso espera a disco.

## Reproducción y aislamiento

Se conservan las sesiones GPU rechazadas. Para aislar el fallo se ejecutó `benchmark_storage.py` del checkout, con la imagen fijada por digest de la última sesión, los mismos componentes turbo/LM 0.6B/VAE/embedding y los montajes del benchmark. Se retiraron `--gpus all` y `--serve`: sólo verifica y copia archivos. El contenedor propio terminó con exit 0 y fue retirado por ID; no se detuvo el engine persistente.

La sonda privada usa `OwnedProcess`, sensores reales y escrituras exclusivas de progreso con `flush`/`fsync`. Mantiene 2 s de deadline por muestra. Se mide por separado codificación, apertura, escritura, sincronización y cierre. No acepta muestras como calibración ni como resultados de matriz.

| Escenario | Resultado |
|---|---|
| 80 escrituras de un progreso conservado, en reposo | `fsync` máximo 0,743 ms; escritura completa máximo 0,992 ms |
| 100 muestras nativas en reposo | 100 completas, cero errores de sensor, navegador visible; máximo 93,6804 ms por muestra |
| 1.400 escrituras de esas muestras | `fsync` máximo 1,0675 ms |
| Preparación Docker + sensores | 278 muestras completas; muestra 279 interrumpida por `worker_deadline` |
| Copia propia | 7.709.380.305 bytes; origen SHA 35,8795 s; copia 33,3220 s; destino SHA 4,9298 s; exit 0 |

La preparación empezó a las 17:25:38 UTC. La interrupción fue durante la copia, alrededor de 17:26:31 UTC, después de verificar el origen y antes de verificar el destino. En el intento interrumpido, el proveedor registró `fsync` de 76, 237, 275, 441 y 443 ms. Los tiempos de apertura/escritura/cierre eran pequeños. El último progreso quedó escrito con los cuatro sensores; su sincronización no alcanzó a producir un retorno supervisado oportuno. Es evidencia de espera por E/S, no de un retorno aceptado.

## Hipótesis probada y decisión

La copia intensiva de pesos compite con los `fsync` de los originales de observación y puede agotar la ventana total. El caso aislado conserva persistencia, sensores, proceso propio y plazo; elimina inferencia y modelos residentes de la reproducción. En reposo no se reprodujo. La prueba no identifica qué componente de Windows/WSL o del almacenamiento físico implementa la congestión.

[ADR-0072](../../../../decisiones/ADR-0072-copia-de-pesos-con-presupuesto-de-io.md) elige limitar la escritura de la copia a 128 MiB/s, con ráfagas de hasta 8 MiB y sin acumular crédito tras pausas. Se conserva toda la verificación y se declara el coste real. Implementación TDD, regresión y reproducción bajo la política nueva están pendientes.

## Evidencia y límites

Artefactos privados en `.cache/dev-cycle/t09/progress-persistence-diagnosis-20261010/`: `native_probe.py`, `receipt.json`, `native-receipt.json`, `native-during-copy.json`, `storage-container.json`, `storage-receipt.json` y los archivos de progreso exclusivos.

Comandos de la sonda:

```powershell
. .\scripts\env.ps1
uv run python .cache/dev-cycle/t09/progress-persistence-diagnosis-20261010/native_probe.py
uv run python .cache/dev-cycle/t09/progress-persistence-diagnosis-20261010/native_probe.py --count 300 --output native-during-copy.json
```

La segunda orden se ejecutó con el contenedor de preparación vivo, confirmado por `docker inspect`. El contenedor terminó después de la interrupción de la sonda. No hubo GPU, spill, calibración, fila de benchmark ni acreditación de matriz. T-09 permanece en progreso. TDD n/a: diagnóstico e informe; el cambio de copia requiere su RED propio.

## Repetición con limitación de flujo

La implementación de ADR-0072 superó TDD, cobertura y revisión A/B/D. La repetición nativa posterior **no pasó**: 378 muestras completas, muestra 379 con `worker_deadline`; un `fsync` del progreso tardó 1.304 ms. La copia limitada terminó exit 0, con 36,067 s de verificación de origen, 93,482 s de copia y 5,242 s de verificación de destino. Los archivos y hashes coinciden exactamente con el primer diagnóstico. El contenedor diagnóstico se retiró por ID después de terminar.

La limitación sí está implementada y registrada; aún no evita las pausas de disco. La hipótesis siguiente es que el flujo por bloques sin sincronización permite acumular páginas pendientes en el disco virtual. Un experimento separado ejecuta `flush` y `fsync` del destino tras cada bloque, manteniendo el límite y todas las verificaciones. No modifica la fuente de producto. Evidencia privada: `sync_copy_probe.py`, `storage-sync-container.json` y salida de la sonda `native-during-synced-copy.json` cuando termine. Hasta ese retorno, la hipótesis no se considera probada.

La primera evidencia de cierre del proveedor interrumpido sólo decía `UNKNOWN_QUARANTINED`, no limpieza confirmada. Una consulta posterior de procesos Windows no encontró el proveedor/sonda; no se transforma el recibo parcial en una confirmación histórica. Ninguna de estas pruebas utiliza la reserva GPU.

## Resultado experimental de sincronización por bloque

El contenedor experimental empezó a las 17:38:58,519 UTC y terminó a las
17:41:26,482 UTC con exit 0. Copió los mismos archivos y SHA-256 del primer
diagnóstico. Verificación de origen: 51,983 s; copia: 91,421 s; verificación de
destino: 4,328 s. La envoltura privada registró 941 bloques, con `fsync` máximo
230,537 ms y suma de sincronización 37,381 s.

La sonda concurrente completó **1.000/1.000** muestras, máximo 342,964 ms. Su
recibo declara `CLOSED_CONFIRMED`, `resources_returned=true`, lectores/escritor
terminados y sin errores de limpieza. El contenedor diagnóstico propio se
retiró por ID después de comprobar su estado terminal. Se conservan los
originales y el resultado negativo anterior.

Esta prueba usa una envoltura experimental alrededor del código de copia;
su recibo aún identifica la política v1 original, por lo que no se presenta
como aceptación del producto. ADR-0072 añade sincronización por bloque y una
identidad de política v2. El siguiente gate es su RED/GREEN, revisión y
repetición directa del producto, sin envoltura. Ningún resultado de esta
sección acredita generación musical ni la matriz GPU.

## Reproducción directa del producto

Después de RED/GREEN, revisión A/B/D sin defectos y QA CPU independiente,
se repitió la preparación sin la envoltura experimental. La fuente
`792c780abc79521653374c3e6acc36f41ac033f7f2bd3571db851cfcca3c39a7`
se montó en el contenedor y conservó su SHA después de la prueba. El
recibo declara `monotonic_bounded_sync_v2`; todos los archivos, tamaños y
SHA-256 coinciden con los del primer diagnóstico.

El contenedor estuvo vivo desde las 17:52:44,791 hasta las 17:54:52,903 UTC
y terminó exit 0. Origen: 35,056 s; copia: 88,931 s; destino: 3,941 s.
La sonda concurrente completó **1.000/1.000**, sin errores de sensor ni
navegador invisible; máximo 255,4281 ms. El cierre declara
`CLOSED_CONFIRMED` y `resources_returned=true`. Se conservan los recibos
`native-during-product-copy.json`, `storage-product-receipt.json`,
`storage-product-container.json` y `storage-product-terminal.json` en el
directorio privado anterior. Se retiró sólo ese contenedor propio, por ID.

Este resultado valida la corrección en la reproducción acotada. No promete
tiempo real en cualquier disco ni acredita audio, spill o matriz GPU. La
sesión nueva `01M4KF9XPEXY1GFA6RCSN9WHTR` conserva los 160 trabajos y fija los
hashes actuales; su ejecución y aceptación siguen pendientes.
