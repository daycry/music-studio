# T-08 — fallo de preprocesamiento CLAP confirmado en CPU

Fecha: 2026-10-06. Investigación sobre la entrega CPU original, sin modificar producto ni cargar pesos del modelo. [Recibo del diagnóstico](clap-preprocessing-diagnosis-receipt.json). No es inferencia CLAP, QA ni aprobación de T-08.

El `ClapProcessor` real instalado en la imagen fijada rechaza los kwargs actuales de `LocalBackend.run`: `truncation=False`, pensado para conservar texto, también llega al extractor de audio. Con la muestra privada de 30 s falla con **`NotImplementedError: data_truncating False not implemented`**. El traceback identifica `processing_clap.py:72`, `processing_utils.py:594` y `feature_extraction_clap.py:238/337`.

Separar las dos llamadas pasa en CPU: `feature_extractor(..., sampling_rate=48000, return_tensors="pt", padding="repeatpad", truncation="fusion")` y `tokenizer(..., return_tensors="pt", padding=True, truncation=False)`. Los modos de audio están documentados en el código upstream instalado. La unión de los tensores conserva `input_features`, `is_longer`, `input_ids` y `attention_mask`, con formas `[1,4,1001,64]`, `[1,1]`, `[1,5]` y `[1,5]`. El texto del probe tiene cinco tokens frente al límite de 512; no se ha truncado.

El audio original de 24 kHz se remuestreó a 48 kHz para el extractor. La ventana del modelo y su estrategia de fusión siguen siendo las del procesador; esta prueba no demuestra que una sola ventana represente íntegramente 30 s ni mide calidad musical.

| Fuente del probe | SHA-256 / revisión |
|---|---|
| Imagen Docker | `37e935536f52f3410f98e824c4d7f85b2ed26c1d3074ad0eabb4ea2692d478e1` |
| Backend original | `3a033ae8adb384cc71552108fa39a6956b205170101375fbef93bcfb424e147d` |
| Fixture privada | `c2f603a9921487bc1421f9d107be3e41e36453b56c4bd0de032f2ff7b2d82f3e` |
| Lock de modelos | `a6874200535337a2236004aa24a535603110a19b4499e743bc73431518f49e4e` |
| Revisión CLAP | `a0b4534a14f58e20944452dff00a22a06ce629d1` |

El recibo y traceback privados se conservan en `.cache/dev-cycle/t08/clap-preprocess-probe/report.json` y `current_kwargs-error.txt`. Los ocho recursos del procesador fueron verificados contra el lock. CUDA permaneció sin inicializar antes, después de ambas pruebas y al terminar; sin red, `--gpus`, `ClapModel` ni inferencia de pesos. `models/` y `data/` se montaron de solo lectura. El producto mantiene su SHA original.

El hallazgo se ha remitido al revisor B, cuyo handle sigue vivo; la revisión completa aún no se ha fusionado. Antes de corregir, registrar el veredicto y un RED que ejecute la ruta de producción con el procesador real y audio sintético, sin pesos ni CUDA. Después, separar kwargs de audio/texto, conservar la validación de longitud, generar nuevos recibos y pasar revisión y QA. Los recibos de la entrega original se preservan como antecedentes.
