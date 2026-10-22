**Lente D — intento 2/3: ✗. Un nuevo gap Important.** Revisión estática exclusivamente del paquete INLINE completo; sin herramientas, pruebas propias ni verificación de hashes.

| Criterio | Resultado | Evidencia |
|---|---|---|
| R09-T01: adquisición y publicación bajo presupuesto original | ✓ | `benchmark_episode.py:548`, `:568`, `:619`; proceso aislado y reserva de cleanup en `benchmark_process.py:362`. Los siete bloqueos aportados ejercitan etapas reales. |
| R09-T02: preparación prolongada observada sin reiniciar cadena | ✓ | `benchmark_coordinator.py:126`, `:174`; `benchmark.py:62`. Tests aportados de preparación de 3 s y continuidad del mismo sampler. |
| Espera de readiness compatible con muestreo independiente | ✓ | `benchmark.py:95`; sampler separado en `benchmark_coordinator.py:44`. |
| Auditoría compatible con el volumen de una matriz completa | ✗ | D-03: transferencia repetida del historial completo y límite acumulativo. |

| Gap | Gravedad | Fichero:línea | Escenario de carga y efecto |
|---|---|---|---|
| **D-03 — auditoría acumulativa excede su límite durante sesiones largas** | **Important** | `scripts/eval/benchmark_coordinator.py:409`, `:426`; `scripts/eval/benchmark_runtime.py:830` | Cada auditoría copia y serializa **todos** los recibos, intentos y registros, y los transmite mediante RPC secuenciales de 1200 caracteres. `benchmark.py:364` y `:395` lo hacen dos veces por cada una de las 160 ejecuciones. Con 160 jobs que duren 300 s de pared —dentro del timeout permitido—, la cadencia nominal acumula unos **48 000 episodios**, además de preparación y auditorías. Cada recibo aparece tres veces en el snapshot: `receipts`, `attempts` y `records`; solo esas copias superan ampliamente **64 Mi caracteres** con el esquema suministrado. `audit_begin` rechaza entonces con `v3_audit_bound_exceeded`, impidiendo completar el lote. Antes del rechazo, un snapshot de 60 Mi caracteres exige aproximadamente **52 429 RPC secuenciales por auditoría**, retransmitiendo también toda la historia ya auditada. |

**Nuevos: Critical 0 · Important 1 · Minor 0.** R09-T01/R09-T02 quedan reevaluados favorablemente para esta candidata CPU en lente D; se conservan sus dos Important históricos y el contador de intento 2/3. Su cierre corresponde al orquestador tras QA. La limpieza histórica continúa sin acreditar; este veredicto no acepta GPU, matriz real ni cierre de T-09.