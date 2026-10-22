# T-08 — entrega de implementación CPU

Fecha: 2026-10-06. Implementer fresco, brief determinista y TDD. Entrega parcial de T-08, sin sustituir revisión, QA ni las pruebas GPU declaradas en el ledger. [Recibo de fuentes y resultados](cpu-delivery-receipt.json).

## Qué está implementado

Engine `/v1` en `127.0.0.1:8130`, padre HTTP sin torch y modelos en proceso hijo. Transcripción ASR seguida de descarga y alineación del texto reconocido; nunca usa la letra esperada para reconocer. CLAP, estética y beats devuelven JSON crudo en tmp. El server sigue siendo propietario de BD y post-proceso. Todas las capacidades mantienen verified=false; alineación independiente queda para M3.

La base por digest proporciona Python 3.12.3, torch 2.14.0+cu130, torchaudio 2.11.0+cu130 y torchvision 0.29.0+cu130. Imports reales conformes sin CUDA inicializado. Proyecto/lock uv propios, sin torch en host; apt, fuentes upstream y dependencias fijadas. Safe loaders locales estrictos, recursos verificados y runtime offline. [ADR-0030](../../../../decisiones/ADR-0030-analisis-local-y-alineacion-secuencial.md) recoge la decisión y sus límites.

## Evidencia de implementación

Build final exit0, imagen `sha256:37e935536f52f3410f98e824c4d7f85b2ed26c1d3074ad0eabb4ea2692d478e1`. Pruebas de contenedor sin GPU ni red: **31 passed, 4 deselected, 1 warning**, exit0. El aviso de Starlette es una deprecación del alias BlockingPortal; no se oculta.

Cobertura oficial pytest-cov **307/341 = 90,03 %**. Todo el código del módulo es nuevo; mínimo por fichero **87,50 %**, superior al 80 % exigido. Estos resultados proceden del implementer, no de QA independiente.

| Fichero | Cobertura |
|---|---|
| __init__.py | 100 % |
| adapter.py | 90 % |
| backend.py | 88,07 % |
| descriptor.py | 100 % |
| safety.py | 88,89 % |
| server.py | 87,50 % |

**Beats real en CPU:** clic de 120 BPM, carga estricta del safetensors existente, 61 beats y BPM=120,000000. Un test real passed, tres deselected; sin CUDA ni descargas. La prueba acredita el proceso hijo y unload, sin acreditar los otros modelos ni calidad musical. Ruff, formato de 13 Python y check del lock propio conformes.

## RED previo a implementación

- Descriptores: `test_descriptors_declare_safe_models_cpu_beats_and_unverified_tasks` → AssertionError: Faltan los descriptores del engine.
- Salida cruda: `test_analysis_returns_raw_json_artifact[audio.clap-clap-larger-music-score]` → AssertionError: Falta el adaptador de análisis.
- Residencia: `test_transcription_releases_asr_before_aligning_recognized_text` → AssertionError: Falta el adaptador de análisis.
- Recursos alterados: `test_locked_resources_reject_modified_configuration` → AssertionError: Falta verificación estricta de recursos locales.
- Beats sin CUDA: `test_beats_loading_never_initializes_cuda` → AssertionError: Faltan loaders locales de los cinco modelos.
- Alineador en descriptor: `test_transcription_descriptor_includes_aligner_dependency_weights` → AssertionError: Falta declarar el peso del alineador secuencial.
- Preflight: `test_preflight_rejects_multiple_outputs_and_extra_input_roles` → AssertionError: Falta validación temprana de número de salidas y roles.
- Audiobox BF16: `test_aesthetics_bypasses_unsafe_upstream_setup` → AssertionError: Audiobox debe activar BF16 explícitamente.

Todos registrados el 2026-10-06 y verdes en la suite de 31. ImportError inicial de factoría y UnboundLocalError de fixture no se cuentan como RED válido. TDD n/a para los cambios posteriores de configuración apt, assert de versión de base y prosa README.

## Pendiente y recuperación

Revisión y QA independientes, además de transcripción/tiempos, CLAP y estética reales con GPU. La fixture privada de 30 s procede de una copia de referencia Suno del propietario, convertida por FFmpeg en CPU; fuente y derivado tienen hashes y el original permanece intacto. No incluye texto esperado para ASR. No se publica el audio ni los prompts.

Logs, comandos exactos, cobertura JSON e imports permanecen en `.cache/dev-cycle/t08/implementation/`, identificados por SHA en el recibo. La rama de T-08 está basada en la entrega parcial T-16: no integrar ambas en main como si T-16 estuviera cerrada. Medidor cerrado 00:45:21–01:11:06 UTC, fuente estimada y tokens/coste/horas IA reales desconocidos. La ventana se solapa con trabajo T-16 y no se suma ni atribuye como consumo real. T-08 y M0 siguen abiertos.
