# QA CPU del runner privado /v1 — intento 1

**QA_PRIVATE_RUNNER_CPU_BLOCKED**: dos defectos Important confirmados.

- R10-V1QA-01: el validador acepta recibos sin hashes LM/DiT/CFG obligatorios. 26 pruebas CPU: 25 pasan y una falla con `ValueError not raised`.
- R10-V1QA-02: dos timeouts consecutivos de logs escapan del finally y omiten restauración de Ollama, liberación del lease y guardado del recibo. Dos sondas CPU aisladas confirman el camino normal y el fallo.

Root verificó 74 artefactos. Fuente congelada 59, protegidos 32 y entrega 15 intactos. No se ejecutó main, GPU, Docker, modelos ni E2E.

Los intentos de harness anteriores se conservan; errores de fixture y la expectativa retirada de igualdad de hashes opacos no son defectos del producto.

Corregir en un runner privado derivado, conservando el original y los recibos de CPU; después QA independiente. La captura runtime del adapter permanece aprobada y este fallo no demuestra un error musical del producto. T-10 y el objetivo M0–M5 siguen abiertos.
