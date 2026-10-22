# T-09 — Revisión del presupuesto de copia, intento 1

Alcance: delta exacto de `benchmark_storage.py` desde la preimagen y nuevo `test_benchmark_storage_pacing.py`, contra ADR-0072. Tres revisores de contexto fresco, de sólo lectura, ejecutaron A, B y D. C no seleccionada por el selector oficial; D seleccionada por `sleep` bloqueante. No es una revisión del hito completo.

| Criterio | A | B | D | Evidencia |
|---|---|---|---|---|
| Copia limitada a 128 MiB/s y 8 MiB | ✓ | ✓ | ✓ | Constantes y presupuesto monotónico por bloque |
| Presupuesto entre archivos sin crédito por pausas | ✓ | ✓ | ✓ | Pruebas de pausa entre archivos, escritura lenta y retorno anticipado de espera |
| Hashes, capacidad, bytes y layout conservados | ✓ | ✓ | ✓ | Verificación antes y después, corrupción rechazada, vecinos intactos |
| Brazo `bind` sin copia ni espera | ✓ | ✓ | ✓ | Recibo con campos de copia nulos y prueba específica |
| Tiempo real y política de copia explícitos | ✓ | ✓ | ✓ | Campos aditivos del recibo; las esperas siguen en `copy_s` |
| TDD y cobertura | ✓ | ✓ | ✓ | Seis RED previos, 7 focales + 4 vecinos; 93/111 líneas = 83,78 %, cero exclusiones |
| Plazos de preparación | ✓ | ✓ | ✓ | Espera en el entrypoint Docker antes de uvicorn; `readiness_s=3600`; coste mínimo de los bytes diagnósticos ≈57,44 s |
| Validación bajo copia nativa | pendiente | pendiente | pendiente | Reproducción programada después de la revisión; no sustituida por tests CPU |

**Veredicto del componente:** 0 Critical, 0 Important y 0 Minor. Revisor A comprobó 45/45 artefactos, fuentes y tests vecinos por SHA-256; el diff coincide con la preimagen. A y B repitieron independientemente 11 pruebas seleccionadas; D repitió las 7 focales. A repitió Ruff y format-check, ambos exit 0.

El clasificador oficial aplicado a los cinco paths del componente devuelve 5 en alcance, 0 fuera y 0 excluidos. El `scope-check` del checkout completo conserva 459 paths de trabajo preexistente fuera del ledger M0, incluido M1; no se declara gate global verde. No se modificaron ni se excluyeron esos paths para aprobar este componente.

## Evidencia RED

- `test_copy_paces_every_chunk_across_files_and_preserves_hashes`: siguiente escritura antes de consumir el presupuesto.
- `test_prior_and_between_file_pauses_do_not_credit_later_writes`: copia sin ritmo tras pausas.
- `test_short_and_spurious_sleep_returns_recheck_deadline`: ausencia de espera efectiva.
- `test_slow_write_does_not_credit_the_following_chunk`: falta de presupuesto para el bloque posterior.
- `test_receipt_declares_copy_policy_rate_and_chunk`: política ausente.
- `test_bind_does_not_copy_or_sleep_and_declares_no_copy_policy`: campos nuevos ausentes.

Cada RED conserva JUnit con un fallo asertivo, cero errores y terminal exit 1, anterior al primer GREEN. Evidencia privada: `.cache/dev-cycle/t09/storage-pacing-20261010/`, con preimagen, diff, inventario, terminales, JUnits y cobertura oficial. La fuente revisada es `0f279c6be74e667363988ae41e9b4b0c0e40db3cc9a18a442ce93b83b0486e85`; el test, `51640baa51d432a6210879a8794b99ae9a1f532abf21ce112ca95a2849b7ebf3`.

T-09 permanece en progreso. Ninguna revisión acredita calibración GPU, matriz160, escucha, aceptación M0 ni cierre de rama.
