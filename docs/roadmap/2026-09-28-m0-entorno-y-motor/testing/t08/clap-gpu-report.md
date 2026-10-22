# T-08 — CLAP corregido: scoring real GPU conforme

2026-10-06. [Recibo](clap-gpu-receipt.json). [Revisión A+B+C](integration-review-1.md) sin gaps; [QA CPU independiente](integration-qa-report.md)47verdes, cobertura90,58% global/88,94% backend. Root corroboró21fuentes/14artefactos históricos/19evidenciasQA, imagen7d0733f y fixture30sSHA antes de cargar y después de terminar.

Una prueba real, sin dobles: `tests/test_gpu.py::test_clap_real_audio_returns_finite_cosine_similarity`, imagen actual por Compose, contenedor propio `--rm --no-deps`, fixture privada autorizada30s, requesttext sintético «Music with singing». Exec27104 terminóexit0: **1passed,1avisoStarlette,36,65s**. El test comprueba score finito en[-1,1], texto sin truncamiento, proceso hijo distinto del padre y unload que termina ese hijo. Usa los pesos locales fijados y el pipeline productivo completo, incluido el cálculo de embeddings. Esta evidencia supera el prefijo CPU; no demuestra similitud artística con Suno ni obediencia a todas las instrucciones de una canción.

Baseline y posterior1314MiB/Ollamavacío. Contenedor propio ausente tras `--rm`; servicio8101 antiguo preservado. No había modelo Ollama que restaurar. No se midió picoVRAM ni spill, ni se generó audio nuevo. Se mantiene la ventana nativa10s/rand_trunc, sin afirmar cobertura completa del fragmento.

El rojo GPU1 anterior y todas las revisiones CPU históricas quedan preservados. CLAP está corregido y verificado en su alcance; ASR todavía necesita diagnóstico y ejecución exitosa. Los CA completos/T08/M0 siguen abiertos. T16fix de ramasDiT continúa separado enCPU, sin otra cargaGPU simultánea. Sin aprobación de calidad musical ni cierre del objetivo del roadmap.

