# T-08 — fix1 CPU: preprocesamiento CLAP real

Fecha: 2026-10-06. Corrección de R-CLAP-01 y R-CLAP-02 de la [pasada 1 incompleta](review-1.md). Implementación con contexto reutilizado del implementer original. [Recibo nuevo de fuentes y evidencia](fix1-delivery-receipt.json). No es revisión independiente, QA ni inferencia de pesos.

La ruta CLAP separa el extractor de audio (`fusion/repeatpad`) del tokenizer (`padding=True`, `truncation=False`). Conserva la comprobación de presupuesto de texto y el transporte de sus tokens completos. La ventana se deriva de `nb_max_samples/sampling_rate`, atributos reales del extractor fijado: el probe observó 480000/48000=10 s, sin atributo `chunk_length_s`. La duración del audio sigue separada de la ventana.

Antes de tocar el backend se incorporó la regresión al engine y se ejecutó sobre la imagen histórica: dos fallos reales, dos avisos de deprecación, en3,63s. El caso largo falló con `NotImplementedError: data_truncating False not implemented`; el corto, con `AttributeError: ClapFeatureExtractor sin chunk_length_s`. Se conservaron logs y XML nuevos bajo `fix1/`, además de los antecedentes de investigación. No se cuenta un fallo de fixture o importación como RED.

Después de corregir, los casos largo, corto y texto excesivo pasan: **3 passed en4,00s**. Procesador, extractor y tokenizer son reales; vocabulario/merges y audio son sintéticos; únicamente el forward de embeddings es un doble. El texto excesivo se rechaza antes del modelo. CUDA no se inicializó. La salida estándar del tokenizer avisa al construir el texto excesivo; no es un fallo ni un resultado de inferencia.

La nueva imagen `music-studio/engine-analysis:m0-t08-fix1` es `sha256:80eee31d9121dbc5a9e2530b1b6c303dab4c203a58c9e6060bd32ff9f88a3819`. Build exit0. La imagen histórica `m0-t08`/`37e9355` se conserva; Compose usa el tag del fix para no ejecutar el backend anterior. El ajuste de tag es configuración, TDD n/a, con comprobación de resolución sin levantar servicios ni exponer variables de entorno.

| Verificación de implementación | Resultado |
|---|---|
| CPU en la imagen nueva | 33 passed, 4 deselected, 1 warning, 7,12s |
| Cobertura oficial del código analysis | 309/343 = 90,09 %; gate80 pasado |
| Mínimo por fichero | 87,50 % |
| Ruff / formato | Conformes; 14 Python formateados |
| Lock propio | Conforme, 111 paquetes |
| Test real en host sin torch | 1 skipped explícito; sin instalar torch |

El único aviso de la suite es la deprecación de `BlockingPortal` en Starlette. La prueba CLAP basada en procesador simulado se retiró en favor de la integración real. La caché y temporales de pytest usan un destino escribible. No se repitió la suite430 ni el modelo beat: su código no cambió; su evidencia original sigue como antecedente, no nueva ejecución de esta imagen.

La revisión2 debe cubrir las correcciones y todo el alcance B que quedó incompleto, conservando A/C anteriores solo para lo que no cambió salvo nueva evidencia. Después corresponde QA independiente y la Verificación GPU completa de T-08. Los criterios siguen abiertos y el descriptor sigue sin capacidades acreditadas por inferencia. No hay calidad musical ni puntuaciones CLAP reales nuevas, ni cierre de M0.
