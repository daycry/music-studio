# QA independiente actual del diario puro

ROOT acepta este componente tras revisión fresca A/B del intento 2 sin defectos pendientes, QA independiente y adopción de tres archivos con SHA idéntico al candidato revisado. **T-05 y M1 siguen abiertos.**

| Comprobación | Windows | Linux CPU |
|---|---:|---:|
| Suite completa del codec | 208/208 | 208/208 |
| Regresión del parser de recibos aceptado | 3/3 | 3/3 |
| Fallos, errores y omisiones | 0 | 0 |
| Cobertura de todo el módulo | 551/580, 95 % | 551/580, 95 % |
| Exclusiones y omits | 0 | 0 |
| Gate técnico auténtico JUnit/cobertura | exit 0 | exit 0 |

Ruff check y format check terminaron con 0. Los seis golden v1 de Windows usan el parser aceptado, sin modificarlo. ROOT verificó 74 artefactos sellados, 13 fuentes, imports reales, JUnit originales, integridad de ambos SQLite de cobertura y los 14 archivos regulares del tar binario. La exportación se verificó antes de retirar únicamente el contenedor propio, con Pid 0 y rm 0.

Las 692 líneas observadas del raw no son 692 sentencias: la API pública Coverage.analysis2 confirma 580 sentencias y 29 ausentes. Ambos raw tienen el mismo conjunto observado y sus informes oficiales propios dan 551/580. Se conservan los dos diagnósticos de preparación del verificador; no se modificaron las pruebas ni los raw para corregir esos supuestos.

La implementación corrigió tres defectos reproducidos: estados públicos mutables, equivalencia Python de true y 1 en historial y prefijo publicado, y ValueError sin clasificar al parsear enteros de 5.000 dígitos. Ocho pruebas fallaron antes del cambio y pasaron después. Ambas revisiones comprobaron sus fronteras sin reabrir criterios anteriores aprobados.

| Fuente incorporada | SHA-256 |
|---|---|
| scripts/storage_journal.py | 5db83df2584f419177162054c02eda46c33abcca253bcf3b2130301bec6f6ea5 |
| tests/test_storage_journal.py | 6d40fafdf27cde341583edcd0ebcc0791ee30b8af8ab15fc97974e01ce8067fc |
| storage-durable-design.md | 673cda4f929b66b839a9625c4fd7919e78acc4e8b17f4c4e2dafd81a7fcde162 |

El actor QA escribió informe y sello completos antes de que su mensaje final fallara por límite de uso. ROOT validó la entrega sellada en disco: no se atribuye un mensaje final del actor ni se repiten sus suites verdes. El resultado aceptado procede de esa ejecución independiente real.

Este componente no tiene UI: Playwright qa-gate, capturas y PDF no aplican a esta entrega. No exime la UI del hito ni sustituye E2E/manuales. El parser y las fuentes readonly permanecen intactos. La adopción conserva preimágenes y no modifica Git, SQLite, SMOKE, ACL existentes, WSL ni GPU.

Los originales están bajo .cache/dev-cycle/m1/storage-journal-codec-current-qa-20261010/. Recibos ROOT de verificación, adopción y freeze están en storage-journal-codec-review2-20261010. Las entregas anteriores de 171 y 80 artefactos se conservan intactas.

Continúan pendientes el store nativo, lifecycle/validated/detach, persistencia ext4/VHDX, Range/recovery/backup reales, pruebas E2E, escucha y revisiones manuales, y el cierre Git del hito. La preparación del store detectó permisos de modificación de dos SIDs aún no acreditados; su política debe resolverse antes de afirmar custodia nativa. Véase el [informe global vigente](../current-validation-2026-10-10.md).
