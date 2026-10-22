# Codec de persistencia creativa — QA independiente y adopción del componente

ROOT auditó 236 artefactos SHA, 158 fuentes, 43 imports y preimágenes de las dos fuentes. La ejecución independiente sobre el corte `50e1c0ac/de3a3c20` obtuvo **757 PASS, 0 FAIL, ERROR o SKIP** en Windows. Ruff check y format --check dieron exit 0. Cobertura oficial branch: 601/601 líneas (100 %), 61/62 ramas (98,3871 %), combinado 99,8492 %, sin exclusiones.

Las revisiones A/B del intento3 terminaron sin gaps actuales; A01 y B01 corregidos en intento2 se conservan, B02 corregido en intento3. [Tablas y traspaso completo](creative-persistence-codec-review3-2026-10-12.md).

La QA conservó un intento 756 PASS/1 FAIL: el harness colocó un temporal fuera de la raíz permitida y `confine_path` lo rechazó correctamente. ROOT autorizó únicamente un nuevo directorio temporal dentro del snapshot privado. La ejecución final usa los cinco archivos originales con `--noconftest`; no modifica guardas ni pruebas. Los 158 hashes permanecen idénticos. Los primeros focales 340/683 y una ejecución con conftest quedan como evidencia parcial, separados del resultado final.

ROOT adoptó exclusivamente `apps/server/app/creative/durable_contracts.py` y `apps/server/tests/test_creative_persistence.py` a las 2026-10-12T04:19:36.465658+00:00. Son codec puro y pruebas CPU. La evidencia privada está en `.cache/dev-cycle/m2/creative-persistence-t05-codec-current-qa1-20261012/`; JUnit y raw coverage finales en `component1/final757-20261012T0421/`, con argv/UTC/imports/SHA antes y después.

**T-05 y M2 siguen abiertos.** Pendientes SQL/ORM/migración y guardas de procedencia, API v2/Song v2/importación, publicación durable, biblioteca/backup y regresión M1 real. Esta prueba no acredita Linux, UI/E2E, modelos, GPU, servicios ni producto completo. `qa-gate.json` es un gate CPU privado; no se presenta como salida E2E del plugin.
