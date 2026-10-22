# T-08 — corrección CPU de permisos de caché Triton

2026-10-06. Alcance delegado: Dockerfile/README de analysis, test nuevo de runtime,
solo tag de analysis en Compose. Sin cambios de backend, CLAP, locks o algoritmos.
Sin GPU, pesos de modelos, red en runtime ni instalaciones en el host.

## RED antes de producto

RED: `tests/test_runtime_cache.py::test_triton_default_cache_is_writable_by_runtime_user`
falló con `PermissionError: [Errno 13] Permission denied: '/studio/.triton'` · 2026-10-06.
Imagen exacta `sha256:7d0733f939606e14dda786941e505f3c23e9565272c4d1fd8a83dbc12efc279d`,
UID 10001, `docker run --rm --network none` sin overrides de usuario o caché.
Único montaje: nuevo test RO en su ruta de tests. FileCacheManager real, sin GPU/modelos.
Salida `1 failed in 0.39s`, exit 1, preservada en `red.log` antes de editar Dockerfile.

## Cambio y GREEN

`TRITON_CACHE_DIR=/studio/.cache/triton` en ENV; directorio explícito con 0755 y
propietario engine mediante el chown existente. Runtime sigue USER engine/UID 10001.
README explica caché y actualiza ambos comandos al tag `m0-t08-asr-cache`.
TDD n/a: tag y prosa; configuración Docker cubierta por regresión real.

`docker compose --profile engines build engine-analysis`: exit 0, una construcción.
Imagen final Id `sha256:d20ae562803cb577c290f0229c0df07551a20647be92feca3d678f523b300c62`.
Config digest `sha256:541032614438f29b9c697461cbdd5a0438110d22c2b9e70aa33fb706a74bb9d2`.
La identidad real de Docker se conserva en `image-inspect.json`; ninguna imagen
histórica retaggeada/eliminada y ambos Id antiguos siguen accesibles.

`docker run --rm --network none music-studio/engine-analysis:m0-t08-asr-cache uv run pytest tests/test_runtime_cache.py -q`:
`1 passed in 0.37s`, exit 0. Sin override ENV/UID/cache ni montajes.
Test verifica UID10001, FileCacheManager real crea/escribe/lee, ubicación de caché,
ENV por defecto, propietario y permisos0755.

Tests vecinos: mismo `docker run --rm --network none`, token ficticio de tests y
únicamente `models/models.lock.json:/models/models.lock.json:ro`; comando
`uv run pytest tests/test_analysis.py tests/test_runtime_cache.py -q`:
`14 passed in 0.61s`, exit0. Sin pesos, sin inferencia GPU, sin suite global.
Primer intento sin lock dio `7 failed, 7 passed in 0.78s` por FileNotFoundError;
log preservado `neighbors-missing-lock.log`, no contado como RED de producto.

Probe `/probe.py` privado RO: UID10001 y ENV correctos; import inicial engine_analysis
sin torch en sys.modules; imports torch/qwen_asr/beat_this/audiobox_aesthetics
reales con `torch.cuda.is_initialized() == false`; SHA de todas fuentes copiadas
en imagen. Primer probe tuvo ModuleNotFoundError por sys.path del script montado
en raíz, corregido solo en helper privado; no producto ni RED. Archivo vacío del
intento preservado, stderr original observado en tool output.

Ruff `check` del test: `All checks passed!`; formato: `1 file already formatted`,
ambos exit0, usando entorno repo y `uv run --no-sync`. Compose config --quiet exit0.
Cobertura de configuración n/a: no lógica productiva Python modificada; sin
porcentaje fabricado. Las fuentes de CLAP/segmentación y dependencias mantienen
sus SHA previos; el receipt contrasta las 19 fuentes de imagen y 22 del checkout.

## Límites y handoff

Esta entrega acredita caché writable en CPU/configuración de imagen, no transcripción
GPU, alineación, precisión, pico VRAM o ausencia de spill. T-08 permanece abierto;
root coordina revisión independiente/QA y retry diagnóstico ASR. GPU prohibida en
este despacho y no ejecutada. No docs/ledger/Git/knowledge públicos modificados.
Recibo usa rutas relativas a la raíz del repo para `sources` y `artifacts`.
