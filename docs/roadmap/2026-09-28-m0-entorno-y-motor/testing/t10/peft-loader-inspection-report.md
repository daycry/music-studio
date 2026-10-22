# Inspección del loader PEFT instalado

La imagen aislada T-09 `sha256:00c32a76c951a4494a23282edf4e53d946f43f244e0790cbd59e806030bd7f43` contiene PEFT **0.18.1**. Se leyeron cuatro archivos de su distribución mediante un contenedor propio CPU: `runc`, sin GPU, modelos, montajes ni red, raíz de sólo lectura. No se importó PEFT ni torch. El contenedor terminó con código 0 y su eliminación se verificó. [Recibo](peft-loader-inspection-receipt.json).

La licencia del código es [Apache-2.0 en la versión oficial](https://github.com/huggingface/peft/blob/v0.18.1/LICENSE), cotejada con el texto instalado, SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`. Se añadió su fila al catálogo legal; esto no adopta adaptadores ni acredita sus derechos.

En la fuente instalada `peft/utils/save_and_load.py:639`, `load_peft_weights()` prioriza el archivo local `adapter_model.safetensors`. Si falta, la rama de la línea 642 admite `adapter_model.bin`, y la línea 695 llama a `torch_load`. La rama offline de la línea 645 también puede buscar una copia pickle en caché. Por tanto, activar offline no basta para excluir pickle.

La configuración se lee desde `adapter_config.json` si existe; `peft/config.py:255` admite otra ruta mediante Hub cuando falta. El lifecycle de ACE-Step fijado a `dce621408bee8c31b4fcf4811682eb9359e1bc94`, `core/generation/handler/lora/lifecycle.py:269` y `:278`, llama a `PeftModel.from_pretrained()` y `load_adapter()` sin una restricción explícita de esa resolución. Las guardas actuales del loader Transformers no prueban que esta ruta PEFT quede protegida.

**Conclusión de alcance:** esta lectura estática identifica las ramas que el laboratorio debe excluir antes de cargar un LoRA real. No acredita que hayan sido ejecutadas ni que el loader completo sea seguro. Sigue pendiente un artefacto real autorizado, compatible, fijado y sellado, junto con una ruta de carga que falle antes de cualquier fallback pickle/red. Los tests deben comprobar ese fallo y el receipt del runtime debe identificar la ruta efectiva; no basta una bandera o el nombre del archivo. No se habilitó LoRA ni se cargó ningún peso.

Los originales copiados y los logs quedan privados en `.cache/dev-cycle/t10/loader-audit/`. La inspección no alteró las fuentes congeladas de T-09, la imagen, los locks ni los servicios. TDD n/a: inspección operativa de sólo lectura y documentación; las guardas testeables corresponden al implementer y su revisión posterior.
