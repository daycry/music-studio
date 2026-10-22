**Lente B — transición ADR-0039, intento 1/3: ✗, con 2 gaps Important.** Revisión estática del paquete INLINE; no ejecuté herramientas, pruebas ni hashes. Este veredicto se añade al historial T-09.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Contexto sellado, originales antes de clasificación y reconstrucción offline | ✓ | `benchmark_observation.py:1072`, `:956`, `:1020` |
| Un solo reintento completo, sin reutilización parcial ni reenvío de inferencia | ✓ | `benchmark_observation.py:1070`, `:882`; `benchmark_runner.py:54` |
| Presupuesto **total** de 2 segundos | ✗ | B-01 |
| Continuidad durante preparación de recursos | ✗ | B-02 |
| Controles de fase, lifecycle y predecesor | ✓ | `benchmark_observation.py:587`, `:837`, `:933` |
| Política nueva y rechazo de resume con fuentes cambiadas | ✓ | `benchmark_plan.py:237`, `:243` |
| Ruptura de adyacencia shared y confianza limitada | ✓ | `benchmark_runner.py:341`; `benchmark_observers.py:62` |

| Gap | Severidad | Fichero:línea | Escenario concreto |
|---|---|---|---|
| B-01 | **Important** | `scripts/eval/benchmark_observation.py:1071`, `:1100`, `:1121` | El plazo se verifica después de que `observers.sample()` retorne. La evidencia C1 aportada registra **2,0655 s**, rechazo y cero reintentos: demuestra rechazo tardío, pero incumple el presupuesto **total de 2 s** de ADR-0039:12. Además, `completed_*` se captura antes de decidir, revalidar y persistir episodio/aceptación/continuidad; esas operaciones pueden superar el plazo y aun así publicar una aceptación con el reloj anterior. |
| B-02 | **Important** | `scripts/eval/benchmark.py:289`, `:361`, `:373`, `:398` | v2 conserva el predecesor del piloto o grupo anterior, pero ejecuta creación, arranque, preparación y comprobaciones sin muestrear. Cuando ese tramo supera 2,5 s, la primera baseline falla por cadencia aunque los sensores sean válidos. El caso CPU `[3]` aportado acredita el escenario: aborta antes de inferencia y limpia correctamente. La causa introducida es conservar continuidad entre grupos sin observar ese tramo; una preparación legítima prolongada impide avanzar por la matriz. |

**Critical: 0 · Important: 2 · Minor: 0.**

C3 es un paso pendiente de adaptación del piloto privado, sin defecto adicional demostrado. Los 300 casos y la cobertura 90,36 % son evidencia verificada por root aportada en el paquete; no acreditan plazo duro, calibración GPU ni matriz completa.