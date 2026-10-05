# Revisión T-07 — intento 2

2026-10-05, base main11c1884 y archivos nuevos; lentes A+B+D frescas. D se lanzó después de terminar A/B debido al límite de threads concurrentes, sin reusar el contexto de implementación. Scope exit 0, sin avisos ni exclusiones de usuario; C false, D true. Tabla anterior completa traspasada, solo corregido reevaluado salvo nueva evidencia.

| Criterio | Veredicto fusionado | Evidencia |
|---|---|---|
| Técnica, entradas/derechos, audio/publicación/manifest, documentación/constitución | ✓ conservado | A, lectura por archivo; integración mock/FFmpeg verde |
| B1 Ctrl+C, conservación del error, descarga confirmada y protección ajena | ✓ corregido | Mock real loading exit130 idle/loadedNone; 63 tests CLI |
| TDD/cobertura | ✓ | 304/324 = 93,83 %, REDs acreditados |
| Plazo de limpieza global de la generación | ✗ B2 nuevo | A verificó límite del helper; B/D demostraron que generate lo llama dos veces al fallar |
| Escucha del propietario | pendiente declarada | T-07 en-progreso; no se atribuye calidad musical a las pruebas |

**B2 Important, pendiente, deduplicado con D:** scripts/generate.py:412 llama finish_job antes de accepted=False:413; si unload devuelve409 persistentemente tras done, consume300s y finally:536 vuelve a ejecutar con otro deadline300. Reloj sintético B: elapsed_synthetic_s=600.0, unload_requests=6001, first_unload=0.0, last_unload=599.9000000000682, error ENGINE_CLEANUP_TIMEOUT, notes=[ENGINE_CLEANUP_UNCONFIRMED]. Root corroboró ambas llamadas antes del fix. Es nueva evidencia del código corregido, no reapertura de un gap anterior. B1 queda resuelto; el presupuesto por helper no basta para el presupuesto por ejecución.

## Evidencia

A: uv run --no-sync --all-packages python -B -m pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --basetemp=.cache/pytest/review-t07-a2 -o addopts= →63 passed,6 warnings,4,61s; ledger-lint0 incoherencias/7avisos; scope0 sinfuera/avisos; diffcheck0.

B: uv run --no-sync --all-packages pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --basetemp=.cache/review-t07-b2-pytest →63 passed,6warnings,4,64s. Reproducción mediante python -B - con fake_transport success, HTTP409 solo unload y reloj sintético sustituyendo únicamente el reloj del CLI; resultado600s anterior. No se escribe fixture de reproducción pública que no fue entregada.

D: reproducción independiente HTTP fake + reloj sintético → comienzos [0,300], 600s simulados, 6001 unload409 y 18007 peticiones HTTP, 1,232s reales, exit0. uv run --no-sync --all-packages python -B -m pytest tests/test_generate.py -q -k 'cleanup or ctrl_c_during_loading' --tb=short --basetemp=.cache/review-t07-d2-pytest -p no:cacheprovider →14 passed/49 deselected,1,04s. D2 deduplicado con B2, sin otros hallazgos.

Advertencias de cacheprovider y timeout de TestClient declaradas. Jira/Confluence desactivados, journals ajenos preservados. No GPU ni material privado de revisores. 0Critical/1Important/0Minor. Siguiente fix2 y revisión3última; escucha aún pendiente.
