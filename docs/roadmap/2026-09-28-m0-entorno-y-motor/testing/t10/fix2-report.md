# Corrección T-10 — rutas Windows a Linux

R10-07 corregido en la generación de planes nuevos mediante `relative_to(root).as_posix()`. Ningún plan anterior se cambia. [Recibo](fix2-receipt.json).

RED propio: la regresión crea fuentes y un plan real con semántica Windows; falla porque las claves no conservan componentes POSIX. Después del fix, esas claves permiten leer los mismos archivos por componentes POSIX y sus sellos coinciden. El test subprocess existente mantiene comandos y transporte originales y comprueba también la portabilidad del plan emitido.

La primera suite ampliada pasa 80 pruebas, pero el único módulo de producción cambiado queda por debajo del 80 %. Se añaden ocho casos significativos de custodia y guardas de CLI. La suite final pasa **88 pruebas en 6,01 s**, sin fallos ni omisiones; cobertura oficial del archivo cambiado **82,3529 %**. Se conservan los dos JUnit, logs y JSON de cobertura: la repetición se justifica por los nuevos tests y la cobertura insuficiente. Ruff check y formato conformes en los dos archivos.

Root verificó 59 fuentes, 29 artefactos, los planes nuevos y el plan anterior. Sólo cambian un módulo y su test; 57 fuentes permanecen intactas. `.coverage` raíz se preserva. Incidente declarado: la primera invocación Ruff actualizó la caché compartida ignorada; no se revierte ni se afirma que todo el árbol permanezca intacto. Los checks finales usan caché privada.

DONE_CPU_WITH_CONCERNS: pendiente revisión independiente, QA y repetir el preflight Linux real. No hubo Docker, GPU, audio ni modelos por el implementador; no se habilita ninguna capacidad musical ni se cierra T-10.
