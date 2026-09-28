# ADR-0006 · Formatos de pesos admitidos, verificación y pickle

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Hereda D-14 de la documentación archivada. Revisada el mismo día tras la verificación técnica: ahora admite GGUF, trata los pickle de los repos oficiales y el `trust_remote_code`.

## Decisión

1. **Formatos que el runtime puede cargar:**
   - `safetensors`;
   - `gguf`: LLM local y variantes cuantizadas de ComfyUI;
   - `onnx`: herramientas auxiliares.

   Ningún otro formato se carga en ejecución.
2. **`torch.load` y `pickle.load` están prohibidos en el código propio.** Un test recorre `apps/` y `packages/` en busca de esas llamadas y falla si encuentra alguna.
3. **Los pickle de repos oficiales se convierten una sola vez**, en `scripts/fetch_models.py`, mediante `packages/weights/audit_pickle.py`. Ese auditor:
   - analiza los opcodes con `pickletools` sin ejecutar nada y rechaza cualquier `GLOBAL`/`REDUCE` que no reconstruya un tensor;
   - convierte a `safetensors`;
   - fija en el lock el SHA-256 del original y el del convertido.

   Casos conocidos: `silence_latent.pt` de cada DiT de ACE-Step, `pytorch_model.bin` de LAION CLAP, `.pth` de Wan (VAE y T5), `.ckpt` de beat_this y `.pth` de Depth Anything.
4. **Cuando el código upstream carga un pickle directamente** (p. ej. `torch.load(silence_latent.pt, weights_only=True)` en ACE-Step), el adapter **parchea esa carga** para que lea el `safetensors` convertido. El parche se documenta en el adapter y tiene su test.
5. **Código remoto (`trust_remote_code`).** Los `.py` que descarga un repo de modelos se fijan en `models.lock.json` con su SHA-256 y se revisan antes de fijarlos. Si el hash no coincide, el engine no arranca. En el manifiesto figuran en `pipeline.remote_code[]`.
6. **Revisión fija.** Cada fichero lleva repo y revisión (commit) de Hugging Face o GitHub, nunca `main`.
7. **Verificación.** El SHA-256 completo se calcula **al descargar**. Al cargar se compara un sello `.verified` (tamaño + mtime + hash). Si el sello no coincide, se vuelve a calcular el hash completo; si ese hash no coincide con el lock, no se carga.
8. **FP8 y NVFP4** no son formatos de fichero sino modos de cómputo. Se rigen por [ADR-0007](ADR-0007-gpu-local-12gb.md).

## Motivo

Cargar un pickle de terceros equivale a ejecutar código remoto. El hash garantiza que el fichero está íntegro, no que sea inocuo. Los repos oficiales incluyen pickle y código remoto, así que ignorarlo habría hecho fallar M0 o habría abierto el agujero sin darnos cuenta.
