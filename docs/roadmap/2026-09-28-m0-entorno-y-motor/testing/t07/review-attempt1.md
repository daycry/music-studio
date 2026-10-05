# Revisión T-07 — intento 1

Fecha: 2026-10-05. Base main=11c1884, diff completo y nuevos archivos declarados. Lentes A+B+D con agentes reviewer frescos, solo lectura. Scope exit 0, sin avisos ni exclusiones de usuario. C no activa; D activa por sleep en publicación. Journals preexistentes ajenos preservados. Jira/Confluence desactivados.

| Criterio T-07 | Resultado | Evidencia |
|---|---|---|
| Material privado y declaración antes de generar | ✓ | tasks.md, recibo own; material literal no leído |
| B-02 preservada y entradas catálogo/directa | ✓ | briefs.yaml y generate.py:55–141; tests de catálogo, entrada y conflictos |
| Semilla, variantes, instrumental, engine y token | ✓ | generate.py:175–272; tests directos/mock/cabecera |
| Progreso real, cuatro archivos y procedencia | ✓ | generate.py:316–451; mock/FFmpeg/verificador reales |
| Verificación CLI completa y mediciones | ✓ | cli-full-generation-receipt.json, exit 0, 255 s, all valid (2 manifests) |
| Escucha y primera impresión | pendiente declarada | T-07 en-progreso; propietario aún no responde |
| Alcance, TDD, cobertura, constitución y docs vigentes | ✓ | A lectura completa, REDs, 263/279=94,27 %, 50 tests; no cambia OpenAPI/interop |
| Publicación sin sobrescribir y rollback Windows | ✓ | Pruebas 5/32, persistencia, colisiones y limpieza |
| Cancelación, descarga y error primario | ✗ | B1 reproducido con mock real |
| Rendimiento y escalado | ✓ | D: 1/8/64 variantes con post stub: 0,011/0,0358/0,2586 s; contrato/manifiesto/rename reales |

## Gap fusionado

**B1 Important, pendiente:** scripts/generate.py:479 intenta unload inmediatamente tras DELETE. Con KeyboardInterrupt después de aceptar jobs mientras loading, DELETE retorna antes del terminal; server.py:389 rechaza unload con 409. Se propaga ValueError ENGINE_HTTP_409 en vez del KeyboardInterrupt original; tras idle el mock conserva loaded={model_id:mock,mode:cpu}. main devuelve 1 en vez de 130. Dos reproducciones CPU con create_mock_app(stage_delay_ms=1000) e interrupción al abrir eventos. No se ha probado una carrera distinta tras un terminal y no se añade ese supuesto. Root corroboró el flujo en generate.py y las funciones cancel/unload del engine común antes de pedir corrección.

## Evidencia ejecutada por las lentes

- A: uv run --no-sync pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --basetemp=.cache/pytest/review-t07-a1 -o addopts= → 50 passed, 3,89 s; ledger-lint 0 incoherencias/7 avisos. Lee cobertura y recibos, sin GPU.
- B: uv run --no-sync --all-packages pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --basetemp=.cache/review-t07-b1-pytest → 50 passed; dos reproducciones CPU anteriores. No se inventa un comando de reproducción que el revisor no entregó.
- D: uv run --no-sync python -B -m pytest tests/test_generate.py -q -k 'publication or mock_post_and_manifest' --tb=short --basetemp=.cache/review-t07-d1-pytest -p no:cacheprovider → 13 passed/37 deselected, 2,13 s; volumen sintético anterior exit 0. Esperas Windows totales ≤1,5 s en CLI síncrona, unload antes del post. Sin hallazgos.

Una advertencia cache_dir desconocida deriva de desactivar cacheprovider. No hay resultado E2E ni GPU nuevo de los revisores. Fusión: 0 Critical, 1 Important, 0 Minor. La escucha impide cierre y está declarada, no es un gap de corrección. Sigue fix1 y revisión intento 2 de 3.
