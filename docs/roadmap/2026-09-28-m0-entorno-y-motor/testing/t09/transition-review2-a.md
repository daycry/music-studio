**Lente A — intento 2/3: ✗. Dos gaps Important nuevos.** Revisión estática exclusivamente INLINE; no ejecuté pruebas ni comprobé hashes. Se conserva el contador y el historial anterior.

| T-09 → criterio | Resultado | Evidencia y límite |
|---|---|---|
| Alcance declarado | ✓ | `tasks.md:401`; `scope-original.json:6` declara los 15 ficheros modificados dentro del alcance. Los otros tres son contexto conservado. |
| R09-T01: adquisición, validación, publicación y verificación bajo presupuesto único | ✓ | `benchmark_episode.py:548`, `:371`, `:382`, `:613`; tests de siete bloqueos reales en `test_benchmark_episode_v3.py:122` y reintento con presupuesto compartido en `:665`. Corrección sustentada estáticamente y por evidencia aportada. |
| R09-T02: observación continua durante preparación | ✓ | `benchmark_coordinator.py:126`; `benchmark.py:62`, `:294`; tests de preparación de tres segundos en `test_benchmark_coordinator_v3.py:407`, `:759`. Conserva sampler y predecesor. |
| Calibración canónica, diez muestras por fase y lifecycle vinculado | ✓ | `benchmark_calibration_v3.py:125`, `:140`; flujo integrado en `benchmark.py:116`; test del builder en `test_benchmark_coordinator_v3.py:857`. |
| Custodia independiente y recomputación de originales | ✓ | `benchmark_coordinator.py:89`, `:409`; `benchmark_episode.py:676`, `:775`; lectura histórica exige digest externo en `benchmark.py:1090`. |
| Timeout de observación conserva el job para reanudación | ✗ | A-03. |
| Fallo del sampler impide publicar una sesión completa, incluido el cierre | ✗ | A-04. |
| Política v3 explícita; interpretación histórica v1/v2 conservada | ✓ | `benchmark_plan.py:208`, `:254`; `benchmark.py:617`, `:1056`. Fixture histórica autorizada en `test_benchmark_integration_cpu.py:34`. |
| Confianza limitada, sin aceptación GPU por pruebas sintéticas | ✓ | `benchmark_evidence.py:242`; pruebas integradas mantienen `valid=false` en `test_benchmark_coordinator_v3.py:1195`. |
| Tests y cobertura | ✓ | Tests sustantivos leídos. Root aporta **416 pass, 5 deselecciones históricas, exit 0**, y **1826/2103 = 86,83 %**, mínimo **82,52 %**, sin exclusiones sobre siete módulos completos. No es cobertura propia del diff ni verde global. |
| Constitución y verificación de tarea cerrada | ✓ | T-09 permanece `en-progreso`, criterios abiertos (`tasks.md:395`, `:407`). No identifico una infracción constitucional adicional; no procede exigir evidencia de cierre. |
| Generados/interop y OpenAPI | N/A | La transición no modifica `commands/`, `agents/`, `hooks/` ni una especificación OpenAPI. |

| Gap | Gravedad | Fichero:línea | Escenario concreto |
|---|---|---|---|
| **A-03 — El timeout destruye el recurso que anuncia conservar** | **Important** | `scripts/eval/benchmark.py:428`; `scripts/eval/benchmark_runtime.py:1099` | `execute_run_v3` escribe `action=query_same_job` y lanza `ObservationTimeout` (`benchmark_runner.py:96`). El `except BaseException` de la sesión lo captura y ejecuta recuperación con `terminate_owned`, que fuerza la eliminación del contenedor. Después, la CLI anuncia consultar el mismo job (`benchmark.py:1260`), aunque su estado en memoria desapareció. Incumple la preservación/reanudación requerida, sin que haya fallado necesariamente el sampler. |
| **A-04 — Un fallo durante shutdown permite publicar `complete=true`** | **Important** | `scripts/eval/benchmark.py:445`; `scripts/eval/benchmark.py:1247` | Tras el último audit, una adquisición todavía en curso puede fallar mientras se cierra el canal o el coordinador. `_sample` registra ese fallo; `coordinator.close()` une el hilo pero no lo propaga. La sesión conserva su retorno de filas y escribe el fallo en el audit final (`:455`); `main` calcula completitud solo con matriz y restauración. Puede publicar `complete=true` y retornar 0 pese al fallo final. La protección de `ContinuousCoordinator.__exit__` no interviene porque esta ruta llama manualmente a `close()`. |

**Critical: 0 · Important: 2 · Minor: 0.** R09-T01/R09-T02 tienen correcciones sustentadas; su cierre formal sigue pendiente de adjudicación y QA. La limpieza histórica continúa **no acreditada**. Este veredicto no acepta calibración GPU, matriz real, ausencia de spill ni cierre de T-09/M0.