# ADR-0016 · ComfyUI como motor headless de imagen y vídeo

- **Estado:** aceptada (pendiente de validar con el spike de vídeo de M4) · **Fecha:** 2026-09-28

## Decisión
- Las funciones de imagen y vídeo se ejecutan en **`engine-comfy`**: portadas, imágenes clave, personajes, I2V, cantante con sincronía labial y reescalado. Es ComfyUI en un contenedor, controlado **solo por su API** detrás de un envoltorio del contrato `/v1`. El usuario nunca ve la interfaz de ComfyUI.
- **Workflows y nodos:**
  - cada tarea (`image.generate`, `image.edit`, `video.i2v`, `video.lipsync`…) tiene un **workflow JSON versionado** en `apps/engines/comfy/workflows/`;
  - su SHA-256 se guarda en el manifiesto (`pipeline.workflow_sha256`);
  - los nodos personalizados se fijan por commit y se revisan antes de añadirlos.
- **Modelos:** viven en `models/comfy/`, con entrada en `models.lock.json` ([ADR-0006](ADR-0006-seguridad-de-pesos.md)).
  - Formatos admitidos: `safetensors` y `gguf`.
  - Los `.pth` de Wan (VAE, T5) y de Depth Anything se convierten con el auditor al descargarlos.
- **Configuración en sm_120:**
  - base PyTorch **cu130**;
  - `--disable-pinned-memory` en WSL2;
  - SageAttention por nodo, no global;
  - `/free` para liberar VRAM y reinicio del proceso si no baja ([ADR-0007](ADR-0007-gpu-local-12gb.md)).
- **FP8/NVFP4:** no se usan por defecto. Solo se habilitan si el spike de M4 demuestra que funcionan en sm_120 con cu130 y que la calidad se mantiene. La decisión se anota en este ADR.

## Motivo
ComfyUI es donde de verdad caben en 12 GB los modelos de 14B, gracias a GGUF, el block swap y el offload asíncrono. Además, los nodos de Wan, InfiniteTalk y Qwen-Image llegan antes aquí que a diffusers. Reimplementar eso serían semanas de trabajo sin ninguna ventaja.

## Riesgos
- **ComfyUI es GPL-3.0.** Mientras corra como proceso aparte y no se distribuya, no plantea problemas en uso personal. Hay que revisarlo en el [gate GC](../legal/comercializacion.md). Salida: reimplementar con diffusers los workflows que se usen.
- **Nodos de terceros:** es código ajeno. Por eso se fijan y se revisan, el contenedor no tiene acceso a la BD y corre offline (`HF_HUB_OFFLINE=1`, sin descargas; no hay aislamiento de red a nivel Docker) ([ADR-0020](ADR-0020-seguridad-local.md)).
- **Actualizaciones:** pueden romper los workflows. Por eso ComfyUI y los nodos se fijan por commit y cada workflow tiene su prueba de conformidad.
