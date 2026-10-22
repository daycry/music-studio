**Sin defectos. 0 Critical · 0 Important · 0 Minor.**

| Criterio de corrección | Resultado | Fichero:línea |
|---|---|---|
| Preservar el cursor ORM compartido; corrección de A3-01 | ✓ Expulsión limitada a la página propia | `admission.py:201` |
| Evitar expulsiones duplicadas o de objetos retry | ✓ Filas únicas y poblaciones disjuntas | `admission.py:55`, `retry.py:98` |
| Conservar prioridad/FIFO, snapshot y comprobación del estado actual | ✓ | `runtime.py:342`, `admission.py:208` |
| Recorrido completo y cierre anticipado | ✓ Regresión con ambas poblaciones de 801 jobs | `test_dispatcher_retry.py:1698` |

Verificación propia de solo lectura: fuentes congeladas coincidentes y cobertura recalculada desde los datos originales sobre el archivo actual: **195/206 = 94,66 %, cero exclusiones**.

Evidencia archivada contrastada, sin reejecutar tests: RED causal `InvalidRequestError` anterior al cambio; final **428 PASS / 2 skips**. SQLite nativo demuestra recorrido exacto de 1602 filas y cierre de ambos lectores con pool en cero; backend sintético y dos suplementos HTTP MockTransport separados.

Dictamen limitado al delta **T04/U2, inspección4**. No concede aceptación de U3 ni de T04 completa.