# B-clock-01 — corrección CPU lista para revisión

Estado: readyreview. No cierra T-09 ni acredita GPU, WDDM real, calidad musical o matriz de benchmark.

El offset mantiene Bias y suma StandardBias o DaylightBias solo si el mes de su fecha está informado. Un único módulo de producción cambiado; sin umbrales, fallback, reconversión histórica ni cambios de metadata/precisión/política.

RED: scripts/eval/tests/test_benchmark_clock.py::test_timezone_offset_ignores_seasonal_bias_without_its_transition_date[0-0-0-0-0] falló con AssertionError (-36000000000 != 0) · 2026-10-07T01:07:23.474534+00:00

Rojo propio antes de editar producción: 1 failed, exit 1. Verde dirigido: 8 passed, exit 0. Ocho casos cubren UTC sin DST, ajustes base con signo, estados 0/1/2, temporada activa con fecha y fecha de la otra temporada que no habilita el ajuste.

Suite inicial: 214 passed + 1 failed / 215, exit 1. El fixture PDH declaraba id2 y conversión UTC+2 pero fechas cero; se conservan suite.junit.xml, coverage.json y stdout/stderr originales. Root amplió exclusivamente el alcance a esas dos fechas; no se reutiliza ese fallo como RED causal.

Suite final tras la última edición y formato: 215 passed, exit 0 (2026-10-07T01:09:02.931483+00:00). Once archivos benchmark. Cobertura oficial pytest-cov del módulo completo: 47/49 líneas = 95.91836735 %, sin exclusiones ni filtro por diff. Ruff: All checks passed!; formato: 4 files already formatted; ambos exit 0.

Cada ejecución guarda argv, exit, UTC real y stdout/stderr originales SEPARADOS, entorno UTF-8. COVERAGE_FILE privado en ambas suites; basetemp/cache privados; uv --frozen --no-sync --all-packages e intérprete gestionado después de scripts/env.ps1. Conversión local y snapshot de zona se prueban con ABI falsa; no colección real de GPU/memoria/navegador, sensores, Docker/WSL/Ollama, red, instalaciones, locks, Git, docs o ledger.

Freeze auténtico: los 66 preimages preparados por root coinciden con sources-freeze.json. Delta exacto: cuatro archivos autorizados; 62 fuentes sin cambio. 12 documentos sin cambio. .coverage raíz conserva bytes 53248 / SHA-256 153490fc264e69bcc7573506ab68a41a109bbdd7bcf6583d0915bdcd84c5d32d (baseline recibido de root y verificado localmente después). freeze-before.json es checkpoint posterior al nuevo test y anterior al código, no baseline inicial.

Entrega: receipt.json, evidence-seals.json, sources-after.json, docs-after.json, freeze-after.json, isolated.diff. No inventario de temporales/fixtures/cache. Root acepta, publica y cierra meter/ledger. Revisión fresca y QA pendientes; verificación de T-09 requiere ejecución GPU/matriz que está fuera de este despacho.
