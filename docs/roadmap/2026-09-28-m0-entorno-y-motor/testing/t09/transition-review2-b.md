**Lente B — intento 2/3: ✗. Tres defectos Important.** Revisión estática del material INLINE; sin ejecutar pruebas ni comprobar hashes. Se conserva el contador y el historial de R09-T01/R09-T02.

| Criterio | Resultado | Evidencia |
|---|---|---|
| R09-T01: adquisición, publicación y verificación bajo el plazo original | ✓ | `benchmark_episode.py:548`, `:613`; bloqueos CPU aportados por root |
| R09-T02: sampler persistente durante preparación y ejecución | ✓ | `benchmark_coordinator.py:126`; `benchmark.py:318` |
| Snapshot coherente de recibos y muestras | ✗ | B-01 |
| Relectura histórica v3 con ancla externa | ✗ | B-02 |
| Fallo del sampler durante cierre impide publicar éxito | ✗ | B-03 |
| Recuperación por ownership sin repetir create/POST | ✓ | `benchmark_runtime.py:774`, `:1097` |

| Gap | Gravedad | Fichero:línea | Escenario concreto |
|---|---|---|---|
| **B-01** | **Important** | `scripts/eval/benchmark_coordinator.py:145`, `:146`, `:410` | `_sample` publica primero recibos/intentos mediante `_custody(phase)` y después añade el registro mediante otra llamada que adquiere nuevamente el lock. Una auditoría puede capturar el snapshot entre ambas: incluye el nuevo recibo pero carece de su registro. `BenchmarkOperationProvider` reconstruye una muestra adicional y falla en `benchmark_runtime.py:871` con `v3_audit_summary_mismatch`, abortando una sesión válida por una carrera interna. |
| **B-02** | **Important** | `scripts/eval/benchmark.py:1125` | `finished_session` entrega `receipts[-1]["observed_utc"]`, una cadena JSON, como `now`. `benchmark_observation.py:85` llama a `value.isoformat()` salvo que sea `Fraction`. Con un cierre v3 legítimo y digest externo correcto, la validación termina en `AttributeError`, convertido en `auto_prerequisite_incomplete`; la relectura histórica falla. El test aportado sustituye el validador canónico y no alcanza esta incompatibilidad. |
| **B-03** | **Important** | `scripts/eval/benchmark.py:443`, `:445`, `:455` | Tras la última auditoría, el sampler puede fallar durante `channel.close()` o al cerrar el acquirer. `coordinator.close()` une el hilo pero no propaga `failure`; esa comprobación existe únicamente en `__exit__`, que esta ruta no utiliza. El audit final registra el fallo y `run_session_v3` devuelve igualmente las filas. Si las 160 son válidas y existe `restore.json`, `main` publica `complete=true` y retorna 0 (`:1247`), aunque la relectura posterior rechace ese mismo cierre. |

**Critical: 0 · Important: 3 · Minor: 0.**

Los mecanismos corregidos de R09-T01/R09-T02 reciben conformidad estática; sus cierres quedan pendientes de adjudicación y QA. Los 416 casos y la cobertura son evidencia aportada por root. Esta revisión no acredita limpieza histórica, calibración GPU, matriz real ni cierre de T-09/M0.