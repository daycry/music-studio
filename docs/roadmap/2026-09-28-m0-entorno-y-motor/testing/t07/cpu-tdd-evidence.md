# Evidencia TDD — T-07, 2026-10-05

Estas salidas se observaron antes del código que resolvió cada caso. Rutas absolutas del checkout anonimizadas como `<repo>`.

- RED: `tests/test_generate.py::test_direct_request_and_rights` falló con `assert None is not None` · 2026-10-05. Comando: `uv run --frozen --all-packages pytest tests/test_generate.py::test_direct_request_and_rights -q --tb=short -o cache_dir=.cache/pytest/cache`. Exit 1, `1 failed, 2 warnings in 0.04s`. La función todavía no existía; el harness devuelve None para poder probar ausencia de comportamiento sin ImportError.
- GREEN: tras implementar el lector directo y conservar los bytes de la letra, la misma prueba pasó en la ejecución conjunta con la integración (`1 failed, 1 passed, 1 warning in 0.56s`; el fallo pertenecía únicamente a la integración aún no implementada).
- RED: `tests/test_generate.py::test_mock_post_and_manifest` falló con `assert None is not None` · 2026-10-05. Comando: `uv run --frozen --all-packages pytest tests/test_generate.py::test_direct_request_and_rights tests/test_generate.py::test_mock_post_and_manifest -q --tb=short -p no:cacheprovider`. Exit 1, `1 failed, 1 passed, 1 warning in 0.56s`.
- GREEN: `uv run --frozen --all-packages pytest tests/test_generate.py::test_mock_post_and_manifest -q --tb=short -p no:cacheprovider`. Exit 0, `1 passed, 1 warning in 2.92s`.
- RED: `tests/test_generate.py::test_brief_catalog` falló con `ValueError: BRIEF_CATALOG_REQUIRED` · 2026-10-05. Comando con ese nodeid, `-q --tb=short -p no:cacheprovider`. Exit 1, `1 failed, 1 warning in 0.23s`.
- GREEN: `uv run --frozen --all-packages pytest tests/test_generate.py -q --tb=short -p no:cacheprovider`. Exit 0, `3 passed, 1 warning in 1.98s`.
- RED: `tests/test_generate.py::test_direct_bpm` falló con `SystemExit: 2` y `unrecognized arguments: --bpm 94` · 2026-10-05. Comando con ese nodeid, `-q --tb=short -p no:cacheprovider`. Exit 1, `1 failed, 1 warning in 0.27s`.
- RED: `tests/test_generate.py::test_long_stage_stream_timeout` falló con `assert 30 > 300` · 2026-10-05. Comando con ese nodeid, `-q --tb=short -p no:cacheprovider`. Exit 1, `1 failed, 1 warning in 0.72s`.
- GREEN: `uv run --frozen --all-packages pytest tests/test_generate.py::test_direct_bpm tests/test_generate.py::test_long_stage_stream_timeout -q --tb=short -p no:cacheprovider`. Exit 0, `2 passed, 1 warning in 0.68s`.
- RED: `tests/test_generate.py::test_song_manifest_privacy_and_rights` falló con `assert True is False` para `commercial_use` de una letra `licensed` · 2026-10-05. Comando con ese nodeid, `-q --tb=short -p no:cacheprovider`. Exit 1, `1 failed, 1 warning in 1.85s`.
- GREEN: ejecución del módulo después de registrar la letra como dependencia con derechos/hashes: `34 passed, 1 warning in 3.93s`, exit 0.
- RED: `tests/test_generate.py::test_engine_errors[no_modes-CAPABILITY_UNAVAILABLE]` falló con `IndexError: list index out of range` · 2026-10-05. Comando con ese nodeid, `-q --tb=short -p no:cacheprovider`. Exit 1, `1 failed, 1 warning in 0.41s`.
- GREEN: ejecución final: `38 passed, 1 warning in 4.65s`, exit 0.

Las pruebas adicionales de validación/errores ejercitan comportamiento ya creado tras los rojos anteriores; no se presentan como nuevos ciclos RED. GPU y escucha del propietario no son criterios comprobables con estos tests CPU y no se dan por cumplidos.
