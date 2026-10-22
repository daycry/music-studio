# QA independiente de cinco drivers default /v1

**CPU_QA_PASS**: 89/89, cero fallos/errores/skips; JUnit y434artefactos cotejados por root.

Cinco imports por intérprete separado, 17 casos por driver y cuatro globales. Bindings de semilla, selector e instrumental exactos; SHA64 obligatorios. AST de guardas/cancel/unload/monitor/logs/cleanup idéntico al fix1 aceptado; cambios autorizados limitados a binding de request y aislamiento de recursos.

Se comprueban113sellos del batch y16×5porcase, custodia59/32/16 intacta, cinco CPUreceipts reales registrados y raws vacíos. Recibos sintéticos usados para tests del validador no se presentan como inferencia. Incidencias iniciales del harness CRLF/firmaApiError preservadas; ninguna fue un gap de producto.

No GPU/Docker/UI nueva por QA. Se puede ejecutar cada driver una vez con preflight fresco, secuencial y parando al primer error; aceptación musical y T10 pendientes. [Recibo](v1-defaults-runner-qa-receipt.json).
