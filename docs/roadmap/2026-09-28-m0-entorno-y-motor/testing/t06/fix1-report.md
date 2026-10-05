# T-06 — corrección de revisión, intento 1 (fix1)

Fecha: 2026-10-05. Estado del despacho: **DONE_WITH_CONCERNS**; correcciones B1/B2 verificadas en CPU. La generación real GPU continúa pendiente de autorización y de la condición externa de VRAM. Este recibo no cierra T-06 ni modifica el ledger. El recibo original `implementation-report.md` se conserva intacto.

## B1 — semillas exactas

Reproducido contra `TaskUtilsMixin.prepare_seeds`, extraído mediante AST de la fuente real del commit upstream `dce621408bee8c31b4fcf4811682eb9359e1bc94`: `acestep/core/generation/handler/task_utils.py:19`, conversión `int(float(s))` en línea 37. SHA-256 completo de la fuente: `a5c90c6af54d1eb207cbf79db39535e115361542cb37735ed4359287bd257a66`. El test comprueba este hash antes de compilar únicamente el método. La reproducción permanece en la suite: 9007199254740993 se redondea a 9007199254740992 en el parser original.

RED: `test_large_seeds_exact_distinct_after_real_parser` falló con segunda semilla efectiva 9007199254740992, esperada 9007199254740993 · 2026-10-05. Recibo: `raw/fix1/red-test_large_seeds_exact_distinct_after_real_parser.log`.

`configure_handler` sustituye el parser de la instancia por `exact_prepare_seeds`, sin tránsito por float. Semillas explícitas: enteros uint64 de 0 a 18446744073709551615, o su representación decimal ASCII; cantidad exacta del batch. Rechaza valores fraccionarios, booleanos, negativos, NaN, notación científica, separadores y valores fuera de rango; nunca rellena con aleatorios. El modo aleatorio sólo existe cuando se solicita expresamente; la generación del adapter utiliza `use_random_seed=False`. Se valida `seed + n_outputs - 1` antes de generar cualquier variante, por lo que el desbordamiento no produce artefactos parciales ni fallback. Metadatos y semillas efectivas coinciden.

RED adicional: `test_explicit_invalid_seeds_never_fall_back_random` detectó aceptación inicial de `1_2`, float y bool (3 fallos) antes de endurecer el parser. Recibo: `raw/fix1/red-invalid-explicit-seeds.log`.

Verificación adicional real torch CPU: `torch.Generator(device='cpu').manual_seed(s).initial_seed()` conservó exactamente [9007199254740992, 9007199254740993, 18446744073709551615], exit 0. Recibo y comando completo: `raw/fix1/torch-cpu-uint64.log`. No carga modelos ni acredita generación GPU.

## B2 — clasificación de fallos de VRAM

RED: `test_cuda_oom_status_becomes_vram_exceeded` falló en DiT, LM y generación con INTERNAL frente a VRAM_EXCEEDED · 2026-10-05. Recibo: `raw/fix1/red-test_cuda_oom_status_becomes_vram_exceeded.log`.

Se conserva el status devuelto por inicialización DiT/LM y se examinan `error` y `status_message` de generación. También se capturan excepciones upstream no absorbidas en preparación, carga y generación. Clasificación exacta: tipo de excepción `OutOfMemoryError`, o texto que contenga CUDA/GPU/VRAM junto con `out of memory`, `outofmemoryerror`, `budget exceeded` o `memory allocation failed`, produce VRAM_EXCEEDED. El resto produce INTERNAL. CPU out-of-memory sin identificación GPU conserva INTERNAL. Los EngineError propios, incluida CANCELLED, se propagan.

Los mensajes públicos son constantes por etapa: `VRAM insuficiente durante <etapa>` o `Fallo interno durante <etapa>`. Etapas internas: preparación del modelo, carga de DiT/VAE/text encoder, carga de LM y generación. No se incluye texto upstream, rutas, tokens o traceback en el mensaje público. La suite comprueba retornos OOM, excepciones OOM, presupuesto VRAM, fallos internos y conservación de cancelación.

GREEN B1/B2: 4 passed (`raw/fix1/green-b1-b2.log`). GREEN completo host: 50 passed, 1 skipped (`raw/fix1/green-all-regressions.log`); el skip corresponde al parche sobre upstream instalado, ejecutado dentro de imagen. Ruff check sin hallazgos; ruff format, 10 archivos ya formateados.

## Imagen y verificación final CPU

Build: `docker compose --profile engines build engine-acestep`, exit 0. Exportó capas en 173 s y terminó unpack en 68,9 s. Recibo completo: `raw/fix1/build-final.log`.

- Tag: `music-studio/engine-acestep:m0-t05`.
- Imagen/config ID: `sha256:9934f4f4cc13bdde43f534b961c1fda7620f5cc0b1df67372148b0959e0d2403`.
- Manifiesto: `sha256:833dfe267ec851027fbdab4568dc486087ab6741c34683e0987098313ee73d6a`.
- Índice de manifiestos: `sha256:b7bb3e147166306eaecd62c26660943c1bd41a8e9d8d631fa27c0177e5b4c91d`.

Comando contractual CPU: `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q`, exit 0: **55 passed, 1 deselected, 5 warnings in 13.45s**. Recibo: `raw/fix1/container-cpu-final.log`. Los avisos son deprecaciones upstream torchao/Starlette; la prueba GPU se excluye.

Cobertura final: `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q --cov=adapter --cov=patches --cov=descriptor --cov=engine_acestep --cov-report=term-missing --cov-fail-under=80`, exit 0: **55 passed, 1 deselected, 5 warnings in 14.70s**. Python 3.11.14; cobertura total **92,96 %** (270 sentencias, 19 sin cubrir): adapter 89 %, patches 98 %, descriptor 100 %, factoría 100 %. Recibo: `raw/fix1/container-coverage-final.log`. Son pruebas de CPU/control/contrato, no acreditación de inferencia real, tiempo o VRAM.

## Prueba GPU preparada, no ejecutada

`docker compose run --rm engine-acestep sh -c "STUDIO_ALLOW_UNVERIFIED=1 uv run pytest -m gpu -q -s"`.

La letra sintética de la prueba de 30 s fue creada por el asistente para esta prueba; `LYRICS_DECLARATION` conserva declaración de autoría y procedencia junto al fixture y se imprimirá en el recibo de la generación. No se introduce un campo extra descartable en JobRequest ni se declara la autoría del material privado de Libre. La ejecución sigue pendiente del orquestador: verificar condición de VRAM y autorización antes de cargar modelos. No se ha realizado ninguna nueva operación GPU.

Producción estable para revisión intento 2. No se modificaron Git, ledger, documentación del root ni pruebas/logs T-05.
