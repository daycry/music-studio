# Integración CLAP: corrección mínima CPU

2026-10-06. Rama `m0/t-08-analysis`; sin commits ni ledger. Ownership: engine-analysis, su tag en Compose y esta carpeta privada. Antecedentes review3/QA y diagnóstico original conservados. Método `custom-agents:tdd`, tras causa probada en `gpu1-diagnosis/report.md`.

El backend fuerza actualmente fusión, pero el checkpoint real tiene `enable_fusion=False` y extractor `rand_trunc`. La corrección de una línea respeta `feature_extractor.truncation`; no cambia arquitectura, pesos, dependencias ni locks. El tokenizer sigue `truncation=False`, conserva el texto completo y rechaza exceso de presupuesto. README explica duración original frente a ventana efectiva de 10 s, recorte aleatorio y relleno corto; no inventa timestamp ni cobertura global. Tags de comandos y Compose apuntan a la imagen nueva.

## TDD y verificaciones reales

- RED: `tests/test_clap_prefix.py::test_clap_checkpoint_real_projection_preserves_text_and_window[short_1s]` falló con RuntimeError: Conv2d `[128,1,4,4]` esperaba 1 canal y recibió 4 · 2026-10-06.
- RED: mismo test `[long_30s]` falló por la misma incompatibilidad · 2026-10-06.
- `red.log`: **2 failed in 13.75s**, antes de modificar backend, importado de imagen original inmutable `306e3b0...`. Solo el test nuevo se montó. Recursos reales montados offline; sin pesos ni CUDA.
- GREEN dirigido y vecinos (`test_clap_prefix.py test_clap_real.py test_backend.py`): **8 passed in 13.43s**. Fuente backend corregida montada sobre imagen original; sin reconstruir todavía.
- Suite engine sobre fuentes montadas: **47 passed, 4 deselected, 1 warning in 28.05s**.
- Ruff: **All checks passed!**. Formato final: **16 files already formatted**. Se conservó aviso inicial de formato del test y se corrigió antes de build. Compose config exit 0.
- Único build final: `docker compose --profile engines build engine-analysis` exit 0, tag `music-studio/engine-analysis:m0-t08-clap-integration`. `.Id` definitivo: `sha256:7d0733f939606e14dda786941e505f3c23e9565272c4d1fd8a83dbc12efc279d` (el config digest del log de build `85b8e6...` no es el ID definitivo del índice).
- Suite ejecutada nuevamente dentro de esa imagen final, sin mounts de fuentes: **47 passed, 4 deselected, 1 warning in 27.16s**, exit 0. Aviso conocido de Starlette/anyio.
- Cobertura oficial pytest-cov: **346/382 = 90,5759 %**. Fichero productivo cambiado `backend.py`: **185/208 = 88,9423 %**; llamada modificada ejecutada. Coverage atribuye los argumentos multilínea a la llamada en línea 343; el argumento cambiado está en línea 348, que no cuenta como sentencia ejecutable independiente. La regresión real demuestra su estrategia. Supera el gate de 80 %; JSON completo preservado. El test nuevo se verifica por regresión, no se computa como código productivo.
- Freeze de fuentes y comparación de 18 ficheros realmente copiados a imagen: `image-source-sha.json`, `receipt.json`; original `m0-t08-fix2` sigue `sha256:306e3b0fbc1170ee066e2aed099ef6638ea7dad7faf3ab5b67edfa90e64b70c9`.
- Primer freeze detectó que el argumento multilínea no figura como sentencia independiente en coverage; se corrigió exclusivamente el arnés para comprobar la llamada contenedora ejecutada. Freeze final: **21 fuentes, 18 fuentes de imagen coincidentes, 14 artefactos**. No se cambió producto ni repitió suite/build.
- TDD n/a: cambio de tag Compose y prosa README.

La nueva regresión usa `ClapConfig`/`ClapProcessor` locales reales, tokenizer real, resample productivo 24→48 kHz, BatchNorm BF16, reshape upstream y `ClapAudioPatchEmbed`/Conv2d reales. Verifica entrada `[1,1,1001,64]`, proyección BF16, tokens íntegros y metadatos de duración/ventana para 1 y 30 s. Se dobla exclusivamente el cálculo posterior a esa frontera para dejar terminar la ruta; no acredita embeddings ni score real. El test sintético anterior con extractor fusionado sigue verde y expresa procesamiento portable, no arquitectura del checkpoint local.

## Comandos CPU

Cargar `. ./scripts/env.ps1`. Todos los `docker run` usaron `--rm --network none -e CUDA_VISIBLE_DEVICES= -e NVIDIA_VISIBLE_DEVICES=none`, sin `--gpus`. Primer RED: imagen por SHA original, mount ro de test nuevo y `/models:ro`, `--entrypoint python ... -m pytest tests/test_clap_prefix.py -q`. GREEN montó además el backend corregido ro. Suite previa montó tests/engine ro. Suite final ejecutó fuentes propias de la imagen nueva con `/models:ro`, `/evidence` privado y `STUDIO_TEST_TMP_DIR=/evidence/final-pytest`:

```text
python -m pytest tests -m "not gpu" --cov=engine_analysis --cov-report=term-missing --cov-report=json:/evidence/final-coverage.json -q
```

## Límites

No GPU ni instalación torch host, descarga de pesos, cambios ASR, suite global, QA, score completo o cierre T-08. No se alteró Ollama. Los CA GPU siguen pendientes. Root controla medición global, documentación arquitectónica, ledger y Git. Lista de cambios de esta pasada: `backend.py`, nuevo `tests/test_clap_prefix.py`, README local, únicamente tag del servicio engine-analysis en Compose, y esta carpeta privada.
