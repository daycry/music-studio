# T-05 - regresion worker CPU

Fecha: 2026-10-10

Con `COVERAGE_FILE` apuntando a `.cache`, las pruebas de dispatcher CPU, contratos, snapshots, invariantes de publicacion y planificacion terminan **134 passed en 37,14 s**. El intento inicial sin esa variable produjo un `KeyError` ambiental en la prueba parametrizada de snapshots; repetir con el entorno de cobertura requerido deja la regresion verde. No se presenta como evidencia de persistencia E2E ni de GPU.

## Correccion del arnes

La prueba parametrizada ya tiene fallback local cuando `COVERAGE_FILE` no esta definido. RED: `KeyError: COVERAGE_FILE`; GREEN: snapshots 12/12 y regresion worker 134/134 sin variable externa.
