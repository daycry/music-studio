# ADR-0007 · GPU local única (RTX 5070 12 GB): un modelo residente, tope y descarga reales

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Revisada el mismo día (verificación técnica y revisión de riesgos)

## Contexto

- **Memoria:** la RTX 5070 tiene 12.227 MiB (11,94 GiB), con unos 10,7 GB libres cuando el escritorio de Windows está en marcha.
- **Arquitectura:** Blackwell (sm_120). Necesita PyTorch ≥ 2.7 compilado con cu128 o superior.
- **Clasificación en ACE-Step:** su código (`gpu_config.py`) la pone en el **tier 4** (≤ 12 GiB). Por defecto eso implica LM 0.6B, INT8, offload y `torch.compile`.
- **WSL2:** el driver **ignora** la política que impide pasar a memoria del sistema. Si un proceso pide más VRAM de la que hay, no se produce un error por falta de memoria: el proceso se vuelve unas 10 veces más lento sin avisar.
- **Liberar memoria:** en torch, `unload` no libera el contexto CUDA, que ocupa 0,3–0,5 GB por proceso.

## Decisión

1. **Un trabajo GPU a la vez y un solo modelo en VRAM**, coordinado por el dispatcher entre engines ([ADR-0018](ADR-0018-cola-de-jobs.md)).
2. **Descarga real.** Cada engine ejecuta el modelo en un **proceso hijo**, y `unload` lo termina. El proceso padre no inicializa CUDA. En ComfyUI se usa `/free`; si la VRAM no baja, se reinicia el proceso. Antes de despachar, el dispatcher comprueba la VRAM libre.
3. **Tope por proceso.** Se calcula al cargar: `cap = VRAM libre − STUDIO_VRAM_MARGIN_MB` (512 MB por defecto), aplicado con `set_per_process_memory_fraction(cap/total)`. Nunca es una fracción fija. El pico se registra y, si se acerca al tope o el RTF se degrada, se marca `spilled`.
4. **BF16 por defecto.** El offload a CPU y la cuantización (INT8 con torchao, 4 bits con bitsandbytes, GGUF) son **modos por modelo**, declarados en su descriptor y elegidos según la medición. La configuración automática de upstream se anula y los modos se fuerzan de forma explícita. En ACE-Step: offload, cuantización y `torch.compile` **desactivados** salvo que el benchmark de M0 diga lo contrario.
5. **Configuración inicial de ACE-Step: DiT 2B turbo + LM 0.6B** (la del tier 4). El LM 1.7B y XL-turbo son experimentos de la tarea M0 T-09.
6. **FP8 y NVFP4:** no se usan en los engines de audio. En `engine-comfy` (vídeo e imagen) se permiten **solo si el spike de M4 los valida** en sm_120 con cu130 ([ADR-0016](ADR-0016-comfyui-como-motor-de-imagen-y-video.md)).
7. **Atención:** SDPA de PyTorch por defecto. flash-attn o SageAttention solo si un modelo lo exige y hay build para sm_120. xformers nunca, salvo con `--no-deps`.
8. **Sin `torch.compile` en M0.** Es un experimento opcional de T-09 porque en sm_120 ha dado segfaults.

## Consecuencias

- Los modelos que no caben quedan fuera, o se marcan en [`../arquitectura/modelos.md`](../arquitectura/modelos.md) con «requiere más VRAM».
- El LLM de letras y los modelos de vídeo se turnan con el generador de música. Cada cambio de modelo cuesta el tiempo de carga, que se muestra en la UI.
- Las versiones concretas están en [`../arquitectura/entorno.md`](../arquitectura/entorno.md).
