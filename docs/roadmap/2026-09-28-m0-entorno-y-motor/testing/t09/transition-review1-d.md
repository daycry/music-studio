**Lente D — transición, intento 1/3: 2 gaps Important.** Revisión estática del paquete INLINE; conserva los verdicts anteriores de T09.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Reintento acotado en número, sin espera añadida ni nueva inferencia | ✓ | `benchmark_observation.py:1070`; `benchmark_runner.py:54` |
| Presupuesto total de ejecución ≤2 s | ✗ | D-01 |
| Cadencia compatible con preparación de los 40 grupos | ✗ | D-02 |
| Esperas periódicas descuentan el coste de adquisición | ✓ | `benchmark.py:79`; `benchmark_observation.py:1146`; `benchmark_runner.py:200` |
| Complejidad o trabajo repetido con degradación demostrable adicional | ✓ | Sin otro hallazgo sustentado por este paquete |

**D-01 · Important — el presupuesto limita la aceptación, pero no la duración de adquisición.**  
**Fichero:línea:** `scripts/eval/benchmark_observation.py:1071` y `:1100`.

La llamada síncrona `observers.sample()` termina antes de comprobar el presupuesto. ADR-0039:12 exige presupuesto **total** de 2 s desde la primera adquisición. El recibo C1 aportado acredita **2,065512 s**, con rechazo y cero reintentos: supera el límite en unos **65,5 ms**. Además, una readquisición iniciada con presupuesto restante pequeño ejecuta nuevamente todas las consultas antes de comprobarlo; los comandos del proveedor conservan timeout de 15 s (`benchmark_observers.py:111`). En un tick con proveedor lento, el coordinador puede permanecer bloqueado durante segundos después del plazo, retrasando la observación del job y la reacción al fallo. El rechazo correcto posterior no cumple el límite total documentado.

**D-02 · Important — continuidad v2 atraviesa preparación bloqueante sin muestreo.**  
**Fichero:línea:** `scripts/eval/benchmark.py:289`, `:361`, `:398`; `scripts/eval/benchmark_observation.py:866`.

El diff conserva el predecesor del piloto y elimina para v2 el reinicio previo al baseline, pero mantiene `create/start/wait_health/verify_image_sources` sin observación concurrente. El siguiente baseline exige terminar dentro de 2,5 s respecto al predecesor. El caso CPU aportado con **create de 3 s** demuestra parada antes de inferencia y cleanup propio.

La matriz contiene **40 preparaciones**, incluidas **20 de copia** con verificación de pesos completos. Basta que una preparación supere esa ventana para abortar el lote; una pausa de 3 s puede impedir las primeras **4 ejecuciones** y dejar pendiente el resto de las 160. La causa introducida es enlazar continuidad estricta a través de un tramo que permanece sin muestreo. Esto no implica que toda preparación futura falle; sí demuestra un escenario concreto incompatible con la nueva ruta.

**Critical:** ninguno. **Minor:** ninguno. C3 es un paso pendiente del piloto, sin gap adicional de rendimiento.

Evidencia de ejecución, hashes y cobertura atribuida exclusivamente a root; no ejecuté herramientas ni pruebas. T09 continúa en progreso, sin aceptación de matriz real, calibración GPU, calidad o ganador. Medición de este lote delegada al agregado de root, sin precio propio.