# Corrección B1 de T-14 — validación de enteros enormes

2026-10-05. Alcance exclusivo: `apps/engines/acestep/adapter.py`, `scripts/generate.py`, `apps/engines/acestep/tests/test_shift.py` y `tests/test_generate_shift.py`. No se cambió descriptor, contrato, default, documentación, ledger, GPU, modelos ni datos privados.

## Reproducción y TDD

El orden anterior convertía el entero a float mediante `math.isfinite` antes de comprobar el rango. `shift=10**400` y `shift=-(10**400)` producían `OverflowError` en los dos helpers programáticos. Se añadieron ambos casos a los tests existentes antes de modificar producción.

- RED: `tests/test_generate_shift.py::test_invalid_shift_rejected_before_enqueue[huge-positive]` y `[huge-negative]` fallaron con `OverflowError: int too large to convert to float` en `scripts/generate.py:290` · 2026-10-05.
- RED: `apps/engines/acestep/tests/test_shift.py::test_adapter_rejects_invalid_shift[huge-positive]` y `[huge-negative]` fallaron con `OverflowError: int too large to convert to float` en `apps/engines/acestep/adapter.py:142` · 2026-10-05.

Comando RED, después de cargar `scripts/env.ps1`:

```text
uv run --no-sync --all-packages pytest tests/test_generate_shift.py apps/engines/acestep/tests/test_shift.py -k huge -q --tb=short --basetemp=.cache/pytest/t14-fix1-red -o cache_dir=.cache/pytest/cache
4 failed, 35 deselected, 2 warnings in 0.54s
```

Cambio mínimo: tras verificar el tipo, se comprueba el rango 1–5 antes de `math.isfinite`. Los enteros enormes se rechazan sin conversión a float; se mantienen los errores tipados `EngineError(INVALID_PARAMS)` y `ValueError(INVALID_PARAMS)`. Los tests de rechazo antes de encolar comprueban que no hay POST a `/v1/jobs`.

## GREEN y compatibilidad

```text
uv run --no-sync --all-packages pytest tests/test_generate_shift.py apps/engines/acestep/tests/test_shift.py -k huge -q --tb=short --basetemp=.cache/pytest/t14-fix1-green -p no:cacheprovider
4 passed, 35 deselected, 1 warning in 0.33s

uv run --no-sync --all-packages pytest tests/test_generate_shift.py apps/engines/acestep/tests/test_shift.py -q --basetemp=.cache/pytest/t14-fix1-shift -o cache_dir=.cache/dev-cycle/t14/fix1/pytest-cache
39 passed, 1 warning in 0.39s
```

Se conservan las 35 pruebas previas y se añaden cuatro casos parametrizados. Siguen cubiertos NaN, infinitos, bool, string, null, valores válidos, omisión, propagación, descriptor y manifiesto.

## Suite vecina y cobertura real

```text
uv run --no-sync --all-packages pytest tests/test_generate.py tests/test_generate_shift.py apps/engines/acestep/tests/test_adapter.py apps/engines/acestep/tests/test_review_fixes.py apps/engines/acestep/tests/test_shift.py -q --cov=scripts --cov=adapter --cov=descriptor --cov-report=json:.cache/dev-cycle/t14/fix1/coverage.json --cov-report= --basetemp=.cache/pytest/t14-fix1-coverage -o cache_dir=.cache/dev-cycle/t14/fix1/pytest-cache
153 passed, 1 skipped, 6 warnings in 16.05s
```

`COVERAGE_FILE=.cache/dev-cycle/t14/fix1/.coverage`. Cobertura de statements por archivo: adapter 155/173 = **89,60 %**; generate 319/339 = **94,10 %**; descriptor sin modificar 30/30 = **100 %**. Ambos archivos de producción modificados superan el 80 %. Recibo real: `.cache/dev-cycle/t14/fix1/coverage.json`.

Advertencias: cinco deprecaciones Starlette ya existentes y un aviso Windows/ACL de caché pytest en la suite vecina. El GREEN dirigido desactivó cacheprovider, lo que originó un aviso sobre la opción cache_dir configurada. El skip pertenece al test upstream de contenedor. Ninguno fue un fallo de comportamiento.

```text
uv run --no-sync --all-packages ruff check apps/engines/acestep/adapter.py scripts/generate.py apps/engines/acestep/tests/test_shift.py tests/test_generate_shift.py
All checks passed!
uv run --no-sync --all-packages ruff format --check apps/engines/acestep/adapter.py scripts/generate.py apps/engines/acestep/tests/test_shift.py tests/test_generate_shift.py
4 files already formatted
```

Los logs completos permanecen en `.cache/dev-cycle/t14/fix1/`. B1 corregido y comprobado en CPU; este resultado no cierra T-14 ni acredita generaciones GPU o calidad musical.
