# T-07 — fix2 del presupuesto único de limpieza

Fecha: 2026-10-05. Se corrigió únicamente B2/D2 Important de `testing/t07/review-attempt2.md`. Ownership: `scripts/generate.py`, `tests/test_generate.py`. Sin modificaciones de publicación/audio, contrato, engine común, dependencias, documentación, ledger, Git, material privado o GPU. Se conservaron informes y toma existentes; no se ejecutó replay.

## Confirmación y RED real

El señalamiento era correcto: el camino posterior a done agotaba el plazo de `finish_job`, pero `accepted` seguía true; finally empezaba otro plazo completo.

La regresión atraviesa `generate` completo con `fake_transport` success, artefacto/hash/manifiesto de contrato, HTTP 409 persistente exclusivamente en unload y reloj sintético exclusivo del CLI. Instrumenta las entradas de `finish_job` y conserva una salida preexistente como sentinel. No genera audio ni espera trescientos segundos reales.

```
. ./scripts/env.ps1
uv run --no-sync --all-packages pytest tests/test_generate.py::test_generate_has_one_cleanup_budget -q --tb=short -p no:cacheprovider
assert clock[0] <= 300 + 1e-9
AssertionError: assert 600.0 <= (300 + 1e-09)
stderr: Aviso: ENGINE_CLEANUP_UNCONFIRMED
1 failed, 1 warning in 1.60s
exit 1
```

RED: `tests/test_generate.py::test_generate_has_one_cleanup_budget` falló con `assert 600.0 <= (300 + 1e-09)` al repetir la ventana de limpieza desde finally · 2026-10-05.

## Cambio mínimo y GREEN

Se marca `cleanup_attempted` antes de iniciar cualquier intento de limpieza. Si el intento posterior a done falla, se añade la nota/aviso sanitizado `ENGINE_CLEANUP_UNCONFIRMED`, se propaga el mismo error y finally no inicia otra espera. Si la generación falla antes de haber intentado descargar, finally mantiene la cancelación/limpieza existente y preserva la excepción primaria. Éxito exige descarga acreditada antes de postproceso/publicación. No se modificó el helper, su plazo ni la protección frente a trabajos ajenos.

```
uv run --no-sync --all-packages pytest tests/test_generate.py::test_generate_has_one_cleanup_budget -q --tb=short -p no:cacheprovider
1 passed, 1 warning in 0.91s
exit 0
```

La prueba comprueba ventana única `[0.0]`, reloj simulado ≤300 s, peticiones unload anteriores al límite, excepción `ENGINE_CLEANUP_TIMEOUT` con nota y aviso de limpieza no acreditada, ningún manifiesto/salida parcial publicado y sentinel preexistente intacto. Las pruebas anteriores mantienen Ctrl+C exit130 con mock real y loaded=None, errores primarios por identidad, transporte, trabajos ajenos y publicación Windows.

## Verificación final ejecutada

```
. ./scripts/env.ps1
Python 3.12.14 gestionado

uv run --no-sync ruff check scripts/generate.py tests/test_generate.py
All checks passed!
exit 0

uv run --no-sync ruff format --check scripts/generate.py tests/test_generate.py
2 files already formatted
exit 0

$env:COVERAGE_FILE = '.cache/dev-cycle/t07/fix2-cleanup-budget.coverage'
uv run --no-sync --all-packages pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --cov=scripts --cov-report=json:.cache/dev-cycle/t07/fix2-cleanup-budget-coverage.json --cov-report=term-missing
scripts/generate.py: 312/332 statements = 93,98 %
Coverage JSON written to file .cache/dev-cycle/t07/fix2-cleanup-budget-coverage.json
64 passed, 6 warnings in 7.03s
exit 0

uv run --no-sync --all-packages pytest -m 'not gpu' -q --tb=short -p no:cacheprovider
190 passed, 6 warnings in 17.12s
exit 0
```

Cobertura del fichero cambiado superior al 80 %. El total de scripts incluye herramientas históricas fuera de este fix. Los seis avisos son los ya declarados: cache_dir desconocida al desactivar cacheprovider y cinco avisos TestClient por el timeout explícito; los transportes sintéticos no acreditan una red real bloqueada. La regresión acredita una única ventana de limpieza del CLI; los límites por petición del helper se conservaron.

Entrega lista para revisión 3. No se declara QA independiente, una nueva generación GPU ni cierre de T-07; escucha/ledger/cierre permanecen a cargo de root.

DONE
