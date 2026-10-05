# T-06 — recibo de implementación CPU (2026-10-05)

Producción congelada para revisión. Sin commits ni cambios al ledger por este subagente. La carga/generación GPU y la liberación real de VRAM siguen pendientes de la condición/autorización externa del orquestador.

## Evidencia final

- Build final: exit 0. Tag `music-studio/engine-acestep:m0-t05`; image ID/config `sha256:6fbddce9961c7ac6d3ae4e38dfdc39f947c5fe0607637d7215b03aa1ddc7a75e`; manifest list `sha256:ddf39fe5582ea4dedf89ccc903ef632aed88ef3864674b4c40c73e33b7d4de7a`.
- `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q`: **35 passed, 1 deselected, 5 warnings in 14.50s**, exit 0. `raw/container-cpu-final.log`.
- `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q --cov=adapter --cov=patches --cov=descriptor --cov=engine_acestep --cov-report=term-missing --cov-fail-under=80`: **35 passed, 1 deselected, 5 warnings in 14.71s**, exit 0; Python **3.11.14**, total **92.31%**, adapter **87%**, patches **98%**, descriptor/factoría **100%**. `raw/container-cov-final.log`.
- Host: **45 passed, 1 skipped**, pruebas del adapter y contrato. Ruff **All checks passed!**, formato **11 files already formatted**, contrato **engine-v1.json up to date**. `raw/host-final.log`.
- Componentes locales reales seleccionados verificados por SHA-256 leyendo bytes, sin deserializar modelos: DiT turbo, LM 0.6B, VAE, text encoder, metadatos, .py remotos y silence_latent convertido. `raw/actual-component-hashes-cpu.log`.
- Factoría real dentro de imagen: `/v1` disponible, `torch` ausente de `sys.modules`, supervisor sin proceso. `raw/factory-no-torch.log`.
- Advertencias: deprecaciones upstream torchao/Starlette; no fallo de pruebas. No se afirma que `uv pip check` sea verde (incompatibilidad nano-vllm/flash-attn conocida en T-05; backend forzado PT).

## RED/GREEN por criterio

Todos los RED siguientes son del **2026-10-05**. Los logs individuales se conservan en `raw/red-*.log`; las verificaciones GREEN de cada grupo y la suite final están junto a ellos.

1. RED: `test_adapter.py::test_load_configuration` falló con `AssertionError: Falta implementación adapter`; `test_runtime_load_forces_pt_bf16_and_budget` falló con `Falta carga real del adapter en hijo`. GREEN: opciones explícitas BF16/offload, tier4, PT, cap/total recibido del supervisor, defaults de checkpoint/LM configurables.
2. RED: `test_adapter.py::test_safe_loading_patch` falló con `AssertionError: Falta implementación patches`; `test_verified_components_fail_closed` falló con `Falta verificación de pesos antes de runtime`. GREEN: parche aplicado al método real upstream, SHA previo a compilar y pruebas de faltantes, corrupción, ruta escapada y pesos/código adicionales. El parche nunca escribe ni autosincroniza checkpoints.
3. RED: `test_adapter.py::test_generation_parameters` falló con `Falta implementación adapter`; `test_generate_real_callback_and_cancellation` falló con `Falta generación adapter`; `test_handler_disables_download_autosync_and_estimates` y `test_decoder_step_hooks_are_real_and_removed` fallaron por funcionalidad ausente. GREEN: letra etiquetada, estilo, duración, BPM/keyscale, idioma explícito/default de canción, semilla por salida; callbacks reales y hooks de forwards, estimador de reloj/persistencia desactivados, cancelación por forward y recuperación del flag cuando upstream captura la excepción.
4. RED: `test_adapter.py::test_float32_wav` falló con `Falta implementación adapter` después de corregir la fixture ACL Windows. GREEN: soundfile FLOAT estéreo 48 kHz desde memoria, igualdad exacta de muestras y rechazo de NaN/vacío/formato incompatible. `save_dir=None` impide al upstream guardar audio por torchaudio.
5. RED: `test_adapter.py::test_descriptor_unverified` falló con `Falta implementación descriptor`; `test_contract.py::test_remote_code_descriptor_compatible_and_preserved` falló con `Falta hashes de código remoto opcionales`. GREEN: MIT, literal de 22 palabras autorizado por orquestador, hashes de .py remotos en campo opcional, tareas/features false, descriptor anterior compatible, rutas/hashes inválidos rechazados y JSON Schema regenerado.

RED adicional: `test_adapter.py::test_pretrained_loads_bf16_before_cuda_transfer` falló con `Falta forzar BF16 al deserializar, antes de transferir a CUDA`. GREEN: Transformers recibe `dtype=BF16`, Diffusers recibe `torch_dtype=BF16`, ambos locales y safetensors; no se alteran tokenizer/config. `raw/red-pretrained-bf16.log` y `green-pretrained-bf16.log`.

TDD n/a: metadatos de empaquetado y dependencia pytest-cov, configuración del runner; no tienen comportamiento de producto.

## Fuente real y límites

- Upstream ACE-Step commit `dce621408bee8c31b4fcf4811682eb9359e1bc94`, extraído de la imagen por el orquestador.
- `acestep/core/generation/handler/init_service_loader.py`: único torch.load de la ruta de inicialización identificada, sustituido por `safe_load_file(...)["tensor"]`; hash de fuente `22b41692bcb73fead4c831d16eaef3dda56cc995577f2353d763445dae7362e1`.
- `acestep/llm_inference.py:404` y `core/generation/handler/init_service_loader_components.py`: loaders sin dtype seguido de `.to(device).to(dtype)`, motivo de forzar BF16 al deserializar.
- `acestep/inference.py:503`: `generate_music(..., save_dir=None, progress=...)` y resultado con tensor CPU float32. `generate_music_execute.py:129`: estimador de difusión por reloj, desactivado explícitamente.
- `models/.../modeling_acestep_v15_turbo.py:1928`: bucle fijado, una llamada decoder por paso Euler; hooks para progreso/cancelación real. Los tests CPU de estos hooks prueban el borde del adapter y **no acreditan ejecución del modelo**.
- GPU preparado: `docker compose run --rm engine-acestep sh -c "STUDIO_ALLOW_UNVERIFIED=1 uv run pytest -m gpu -q -s"`. El test real solicita 30 s, comprueba WAV FLOAT/48 kHz/estéreo, duración/NaN/RMS, telemetría y muerte del proceso/liberación VRAM. El opt-in permite las tareas todavía `verified:false`; no habilita suscripciones ni proveedores externos.
- No se ha ejecutado esta prueba GPU ni acreditado carga, audio real, tiempo de generación, pico VRAM o recuperación real de VRAM. El ledger debe continuar `en-progreso`.
