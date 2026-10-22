# QA CPU independiente del runner /v1 — intento 2

**QA_PRIVATE_RUNNER_CPU_PASS**: 17/17 pruebas, 0 fallos y 0 errores. R10-V1QA-01/02 cerrados únicamente para el runner privado CPU.

Se validan 27 subcasos de hashes y el finally exacto frente a timeouts, errores de wait/terminate/kill/join, hilo vivo y monitor no iniciado. La restauración limitada a modelos descargados, la liberación del lease y el recibo se alcanzan; fallos de cleanup mantienen exit1 y el camino normal devuelve exit0. Import real del derivado sin torch; OUT conserva la receta original.

Root cotejó 72 artefactos/JUnit17. Original15/fuentes59/protegidos32/QA74/FIX355 y .coverage intactos. Primera tanda16PASS preservada; se añadió el caso de timeout persistente y se aisló el return de errores API ajenos.

No se ejecutó main, GPU, modelos, Docker, red ni UI. Se puede avanzar a una ejecución autorizada nueva con lease, preflight fresco y guardas; no se ha validado su resultado todavía. No se cierra T-10 ni se marca verified por CPU.
