# QA independiente del piloto v2 (T-09)

35 controles CPU originales pasan; cobertura oficial del módulo completo 173/186 = 93,01 %, cero exclusiones. 310 protegidos, 67 fuentes y 12 documentos intactos. Ruff/formato py312, ledger y qa-gate CPU conformes.

El harness QA omitió los argumentos obligatorios de coverage-check y conservó QA_CPU_FAIL. Root ejecutó solo esa puerta con argumentos correctos: exit0, sin UI y sin degradación. No se repitieron los tests ni se modificaron originales. Nueva calibración GPU y matriz siguen pendientes; no hay ganador musical ni cierre M0. [Recibo](private-pilot-contract-qa-receipt.json).
