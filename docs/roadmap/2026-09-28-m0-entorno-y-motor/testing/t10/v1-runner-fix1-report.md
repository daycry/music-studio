# Corrección privada del runner /v1 — intento 1

R10-V1QA-01/02 corregidos en un runner derivado; el original, su receta, plan, permisos y preflight permanecen intactos. No se modifican fuentes del producto.

Se exigen tres hashes LM/DiT/CFG SHA64 válidos, sin inventar igualdad con preimágenes dinámicas no capturadas. Monitor y subprocess de logs tienen cierres acotados, errores registrados y continuidad hacia restauración de Ollama, liberación del lease y escritura del recibo. Los errores persistentes mantienen exit1.

RED sobre preimagen original: 27 fallos de subcasos de hashes y cuatro excepciones funcionales de cleanup. GREEN final: 25 pruebas, 0 fallos, 0 errores, exit0. Los intentos de aislamiento de fixtures anteriores se conservan; no se atribuyen al producto.

Root cotejó 355 artefactos y JUnit25. Custodia 74 QA / 59 fuentes / 32 protegidos / 15 helpers originales intacta. El import explícito de common conserva OUT original.

Siguiente puerta: QA independiente del derivado antes de GPU. No se ejecutó main, modelo, red, Docker ni UI. T-10 sigue abierta y verified=false.
