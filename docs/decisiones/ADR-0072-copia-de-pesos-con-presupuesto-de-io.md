# ADR-0072 — Copia de pesos con presupuesto de E/S

- **Estado:** aceptada; delta implementado, revisado y validado en reproducción directa; matriz GPU pendiente
- **Fecha:** 2026-10-10
- **Decisor:** orquestador, bajo delegación autónoma del propietario
- **Ámbito:** preparación `container_copy` de M0/T-09

La matriz WDDM v3 vuelve a agotar el presupuesto absoluto de 2 s mientras prepara el segundo grupo. La reproducción aislada ejecutó sólo copia/verificación de pesos en Docker, sin GPU ni servicio de inferencia: 278 muestras completas y un `worker_deadline` en la siguiente. El proceso propio registró `fsync` de progreso de 237, 275, 441 y 443 ms. En reposo, 100 muestras tuvieron máximo de 93,68 ms y los 1.400 `fsync` máximo de 1,07 ms. La copia de 7.709.380.305 bytes duró 33,32 s; el fallo ocurrió durante ese tramo, entre la verificación de origen y la del destino. Esto prueba competencia de E/S de la copia con la persistencia; no demuestra un bloqueo de Edge ni del driver.

Se compararon aumentar el plazo del observador, reducir la durabilidad de los originales y limitar la copia. Se elige limitar la copia: conserva los presupuestos de ADR-0039/0042/0045 y la persistencia real de RAW, progresos y commit. Una copia más lenta debe registrarse como tal, nunca descontarse de `copy_s`.

La preparación `container_copy` limita el flujo de escritura a **128 MiB/s**, con un bloque máximo de **8 MiB**, mediante reloj monotónico y esperas después de escribir cada bloque. El presupuesto es global para los archivos del grupo; no se reinicia por archivo. Se impide que una pausa anterior acumule crédito para ráfagas posteriores. Es un presupuesto de la aplicación, no una garantía física ni de tiempo real. La copia conserva layout, bytes, revisión, SHA-256, comprobación de capacidad y verificación completa antes y después. El recibo declara la política, el límite y el tamaño de bloque. El brazo `bind` no copia ni espera por esta política.

La aceptación requiere RED/GREEN de la limitación y de la conservación de bytes, regresiones de almacenamiento, revisión fresca y repetir la reproducción de preparación con sensores nativos. Si se vuelve a agotar el plazo, se conserva el intento como rechazado y se investiga; no se relajan los umbrales. Esta decisión no acredita la matriz de 160 posiciones ni cierra T-09.

Evidencia privada reproducible: `.cache/dev-cycle/t09/progress-persistence-diagnosis-20261010/` (`native-receipt.json`, `native-during-copy.json`, `storage-receipt.json`, `native_probe.py`).

## Resultado de la primera implementación

TDD, 11 pruebas seleccionadas, cobertura del módulo 83,78 % sin exclusiones y revisión A/B/D conformes. La reproducción nativa de la primera política falló: muestra 379, `fsync` de 1,3 s durante la copia limitada. Se conserva el resultado negativo; no se acredita esta política como solución suficiente del timeout. Se inició un experimento de sincronización de cada bloque para distinguir flujo limitado de acumulación de datos pendientes en el disco virtual; sus resultados y la corrección de producto se recogen a continuación. El ajuste conserva hipótesis probada, RED/GREEN y nueva revisión. La aceptación GPU sigue pendiente.

## Ajuste probado en reproducción aislada

El experimento terminó con **1.000/1.000** muestras nativas completas, máximo
342,964 ms y cierre propio confirmado. Copió los mismos 7.709.380.305 bytes,
con SHA-256 y layout verificados, sin GPU ni servicio de inferencia. Cada uno de
los 941 bloques se vació y sincronizó antes de escribir el siguiente; el
`fsync` más lento de la copia duró 230,54 ms. El límite siguió siendo 128 MiB/s
y 8 MiB por bloque. La copia duró 91,42 s, incluidos los costes reales de
sincronización y espera. Esta reproducción apoya controlar los datos pendientes
de escritura, además del flujo; no garantiza la latencia de cualquier disco.

Se añade **`flush` y `fsync` después de cada bloque escrito**, antes de continuar
con el siguiente. Los errores de escritura, vaciado o sincronización se propagan
y no producen un recibo de preparación válida. La política del recibo cambia a
`monotonic_bounded_sync_v2`, para distinguirla de la primera implementación y
del experimento privado. Se preservan el reloj monotónico, el presupuesto global
sin crédito acumulado, el brazo `bind` sin copia y todas las verificaciones.

Evidencia: `native-during-synced-copy.json`, `storage-sync-receipt.json` y
`sync_copy_probe.py` bajo el directorio diagnóstico anterior. Falta RED/GREEN,
revisión del delta y reproducción usando directamente el código del producto.
La matriz GPU y la aceptación de T-09 siguen pendientes.

## Validación directa del producto

El delta se implementó con nueve RED/GREEN aislados, revisión A/B/D sin
defectos y QA CPU independiente: 19/19 pruebas y cobertura 95/113 = 84,0708 %,
sin exclusiones. La reproducción directa, sin envoltura experimental, copió
los mismos archivos y SHA-256, con política `monotonic_bounded_sync_v2`.
Verificación de origen 35,056 s; copia 88,931 s; destino 3,941 s.

El contenedor terminó exit 0 y se retiró por su ID después de comprobar
ownership. La sonda concurrente completó **1.000/1.000**, sin errores de
sensor y con navegador visible; máximo 255,4281 ms y cierre confirmado.
Se comprobaron los SHA de producto y test antes y después. No hubo inferencia
ni uso de GPU en esta reproducción; no garantiza cualquier latencia futura.

Evidencia privada: `native-during-product-copy.json`,
`storage-product-receipt.json`, `storage-product-container.json` y
`storage-product-terminal.json` en el directorio diagnóstico anterior.
La matriz GPU usa una sesión nueva con estos hashes; sigue pendiente.
