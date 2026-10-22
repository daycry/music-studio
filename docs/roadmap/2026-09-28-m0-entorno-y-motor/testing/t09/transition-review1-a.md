**Lente A — T-09, transición intento 1/3: ✗, 2 gaps Important.** Revisión estática del paquete INLINE; sin ejecutar herramientas ni verificar hashes o pruebas por cuenta propia. Los verdicts anteriores permanecen independientes.

| T-09 → criterio revisado | Resultado | Evidencia |
|---|---|---|
| Alcance: seis módulos y dos pruebas, sin cambios en `/v1`, engines, pesos o dependencias | ✓ | `scope-original.json:5`, sin exclusiones ni avisos; coincide con `tasks.md:401` y diseño:9. |
| Política v2, fuentes selladas y plan nuevo; impedir resume con fuentes cambiadas | ✓ | `benchmark_plan.py:229`, `benchmark_observation.py:515`, `benchmark.py:683`. |
| Original completo persistido antes de clasificar; máximo un reintento fresco; ningún otro fallo recuperable | ✓ | `benchmark_observation.py:826`, `:871`, `:1070`; pruebas `test_benchmark_reacquisition.py:104`, `:151`, `:192`. |
| Presupuesto **total** de 2 s desde la primera adquisición | ✗ | A-01. |
| Continuidad y preparación compatibles con ejecutar la matriz conservada | ✗ | A-02. |
| Validación offline de originales, aceptación, reloj, predecesor y cadena | ✓ | `benchmark_observation.py:901`, `:980`, `:1020`; pruebas de adulteración en `test_benchmark_reacquisition.py:235`, `:278`, `:716`. |
| Calibración: diez aceptadas por fase, límites vinculados al lifecycle real | ✓ | `benchmark_observation.py:389`, `:587`; pruebas `test_benchmark_reacquisition.py:468`, `:671`. La adaptación privada C3 sigue pendiente; no constituye por sí sola un defecto. |
| Sin reenviar inferencia; ownership, cancelación y cleanup preservados | ✓ | `benchmark_runner.py:54`, `benchmark.py:552`; pruebas `test_benchmark_reacquisition.py:760`, `:843`. |
| Shared: romper adyacencia tras rechazo; confianza limitada y ninguna afirmación causal de cero spill | ✓ | `benchmark_runner.py:341`, `benchmark_observers.py:62`, `benchmark_evidence.py:238`; prueba `test_benchmark_reacquisition.py:303`. |
| Tests sustantivos y cobertura mínima | ✓ | Lectura de los tests citados. Root comunica 300 casos y **1312/1452 = 90,36 %**, seis módulos completos, cero exclusiones y todos ≥80 %. No se presenta como cobertura propia del diff. |
| Constitución explícita | ✓ | Sin infracción adicional identificada de `docs/CONSTITUTION.md:17`, `:19`, `:21`, `:24`, `:25`, `:33`, `:44`. |
| Verificación de tareas cerradas | ✓ | No hay cierre que acreditar: `tasks.md:395` mantiene T-09 en-progreso y sus criterios abiertos. |
| Generados/interop y OpenAPI | N/A | El diff no toca `commands/`, `agents/`, `hooks/` ni una especificación OpenAPI. |

| Gap | Gravedad | Fichero:línea | Escenario y requisito incumplido |
|---|---|---|---|
| **A-01 — El presupuesto limita aceptación, pero no duración total** | **Important** | `scripts/eval/benchmark_observation.py:1071` | `observers.sample()` bloquea síncronamente; el plazo se comprueba después de retornar y persistir el original. El recibo proporcionado acredita **2,065512 s**, rechazo y cero reintentos. Esto preserva el rechazo correcto, pero incumple el **presupuesto total de 2 s** declarado en `ADR-0039:12` y diseño:5. Además, validación y escrituras posteriores al reloj de `:1100` quedan fuera de ese cómputo. |
| **A-02 — Continuidad v2 atraviesa preparación sin observación** | **Important** | `scripts/eval/benchmark.py:398` | El cambio restringe el reinicio del predecesor a v1; v2 conserva el último episodio durante `create/start/wait_health/verify_image_sources` (`:361`, `:370`, `:373`, `:380`), sin muestreo concurrente. Una preparación de 3 s provoca rechazo en el primer baseline, antes de inferencia, como demuestra el test proporcionado en `test_benchmark_reacquisition.py:971`. La causa introducida es concreta: continuidad estricta entre grupos sin observar esas operaciones. Impide avanzar en ese escenario de preparación permitido, aunque no demuestra que toda ejecución futura vaya a fallar. Referencias: `ADR-0036:26`, `ADR-0039:14` y diseño:7. |

**Critical: 0 · Important: 2 · Minor: 0.** La matriz real, acreditación GPU, recomendaciones y calidad musical permanecen pendientes; esta revisión no los acepta. Medición y coste corresponden al lote agregado de root.