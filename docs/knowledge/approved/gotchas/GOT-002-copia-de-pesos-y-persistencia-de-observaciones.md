---
id: GOT-002
version: 1
estado: aprobado
project: music-studio
scope: M0/T-09 container_copy CPU-Docker
source: docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/storage-contention-diagnosis-2026-10-10.md
confidence: high
category: GOTCHA
evidencia: validated_case
fecha: 2026-10-10
fuentes:
  - docs/decisiones/ADR-0072-copia-de-pesos-con-presupuesto-de-io.md
  - docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/storage-contention-diagnosis-2026-10-10.md
  - docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/storage-sync-review-2026-10-10.md
tags:
  - "area:almacenamiento"
  - "componente:container_copy"
  - "operacion:fsync"
  - "entorno:docker-wsl2"
---

# La copia de pesos puede retrasar la persistencia de observaciones

Entrada aprobada por `knowledge-curator` el 2026-10-10 como `GOTCHA`, con evidencia `validated_case` limitada al caso CPU/Docker documentado.

## Síntoma y caso aislado

La preparación `container_copy` de pesos coincidió con `worker_deadline` del
observador, cuyo presupuesto absoluto era de 2 s por muestra. La reproducción
usó Docker para verificar y copiar archivos, sensores nativos y escrituras
exclusivas de progreso con `flush`/`fsync`, sin inferencia ni uso de GPU.

En reposo, 100 muestras terminaron sin errores; el máximo fue 93,6804 ms y el
`fsync` más lento de sus 1.400 escrituras fue 1,0675 ms. Durante la copia inicial,
se completaron 278 muestras y la siguiente agotó el plazo. Se observaron
`fsync` de progreso de hasta 443 ms. El caso acredita competencia de E/S entre
la copia y la persistencia; un resultado calculado no equivale a un retorno
supervisado dentro del plazo.

Limitar únicamente el flujo a 128 MiB/s, con bloques de hasta 8 MiB y sin crédito
acumulado, no resolvió el caso: 378 muestras completas, fallo en la muestra 379
y un `fsync` de progreso de 1.304 ms. La copia y su verificación terminaron
exit 0. Ese resultado negativo se conserva como evidencia.

## Corrección validada y uso recomendado

[ADR-0072](../../../decisiones/ADR-0072-copia-de-pesos-con-presupuesto-de-io.md)
añade `flush` y `fsync` después de cada bloque escrito, antes de escribir el
siguiente, conservando el presupuesto global monotónico. El recibo identifica
la política como `monotonic_bounded_sync_v2`. Los fallos de escritura, vaciado
o sincronización se propagan; no producen un recibo válido. El coste de
sincronización y espera forma parte de `copy_s`; el brazo `bind` no copia.

La reproducción directa del producto, sin envoltura experimental, copió
7.709.380.305 bytes con layout y SHA-256 coincidentes con el diagnóstico inicial
y terminó exit 0. La copia duró 88,931 s, además de 35,056 s de verificación del
origen y 3,941 s del destino. La sonda concurrente completó **1.000/1.000**
muestras, sin errores de sensor y con navegador visible; máximo **255,4281 ms**.
El cierre declaró `CLOSED_CONFIRMED` y `resources_returned=true`; el contenedor
propio se retiró por ID tras comprobar su estado terminal y ownership.

La corrección cuenta con nueve RED/GREEN aislados, revisión A/B/D con cero
defectos y QA CPU independiente de 19/19 pruebas. La cobertura del módulo fue
95/113 líneas, 84,0708 %, sin exclusiones. Ante una nueva competencia de E/S,
conservar persistencia, plazo y recibos negativos, y repetir la reproducción
con el código de producto antes de dar por válida una mitigación.

## Límites de la evidencia

La validación se limita a esta reproducción CPU/Docker. Apoya controlar las
escrituras pendientes además del flujo, pero no identifica la causa interna de
Windows/WSL ni un componente del almacenamiento físico. No atribuye el fallo a
Edge ni a drivers, ni garantiza tiempo real o latencias futuras en cualquier
disco. No acredita matriz GPU, audio, spill, calidad musical ni cierre de T-09.

## Evidencias

- [Diagnóstico y reproducción directa](../../../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/storage-contention-diagnosis-2026-10-10.md): controles en reposo, resultado negativo del flujo limitado y prueba del producto.
- [Revisión y QA CPU](../../../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/storage-sync-review-2026-10-10.md): RED/GREEN, revisión A/B/D y cobertura.
- [Decisión de copia](../../../decisiones/ADR-0072-copia-de-pesos-con-presupuesto-de-io.md): presupuesto, política v2, coste real y límites de aceptación.

Los informes identifican los recibos privados reproducibles
`native-during-product-copy.json`, `storage-product-receipt.json`,
`storage-product-container.json` y `storage-product-terminal.json` bajo
`.cache/dev-cycle/t09/progress-persistence-diagnosis-20261010/`.


## Curación

La taxonomía exige `validated_case` para `GOTCHA`. Se verificaron las tres fuentes públicas, QA CPU 19/19, cobertura 95/113 sin exclusiones y los recibos originales de copia y sonda: 1.000 muestras, máximo 255,4281 ms, cierre confirmado. El índice previo contenía cero entradas aprobadas; no hay contradicciones ni se modifica una decisión vigente.

Salida real de `curator-gate.py --decision approve --category GOTCHA --root . --json`:

```json
{"decision": "approve", "categoria": "GOTCHA", "errores": [], "avisos": []}
```
