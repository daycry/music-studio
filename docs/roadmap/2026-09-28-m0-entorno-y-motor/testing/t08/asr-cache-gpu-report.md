# T-08 — transcripción y alineación reales tras corregir la caché

2026-10-06. Un único trabajo GPU de 30 segundos en imagen inmutable `d20ae562…`, fixture privado de referencia del propietario y wrapper/factoría congelados. Terminal `done`, Docker/host exit 0, 114.19 s de reloj. [Recibo](asr-cache-gpu-receipt.json).

Qwen3-ASR produce texto no vacío; el alineador devuelve **87 palabras** con tiempos finitos, monótonos y contenidos en el audio, último final 29.92 s. ASR se libera antes de cargar ForcedAligner. Dos revisiones de modelo fijadas en los stages y alineación del texto reconocido, sin suministrar la letra del propietario.

**Precisión pendiente:** la autodetección devuelve `English` para la referencia del proyecto cuya letra está en castellano. El trabajo no forzó idioma. El éxito de ejecución y los tiempos válidos no prueban que la transcripción sea correcta; no se atribuye WER, fidelidad a la letra ni calidad musical. Hay que contrastar el idioma y el contenido, y evaluar el parámetro de idioma explícito antes de usar el resultado como métrica de fidelidad.

Hijo PID 11, padre PID 1 sin Torch. `unload` termina el proceso, contenedor propio retirado; GPU después 1314 MiB ocupados, Ollama inicialmente vacío. Baseline previo 1314 MiB. No se cambian servicios externos ni originales. Las trazas muestran carga, inferencia, liberación y carga del alineador sin excepciones; evidencia privada en `.cache/dev-cycle/t08/asr-cache-gpu-20261006a/` y salida cruda en `data/tmp/01DBAD4B3D43D84F54BC221837/analysis.json`.

Root revalidó 22 fuentes, dos wrappers y origen de audio preservado. No hay registro de pico VRAM o spill en este harness: esos campos permanecen null. Esta prueba resuelve el fallo real de permisos Triton; no sustituye la Verificación canónica completa de las cuatro tareas, la medición de capacidades ni la evaluación de precisión. T-08 y M0 siguen abiertos.

## Contraste privado de la etiqueta de idioma

[Probe l?xico](asr-language-probe-receipt.json), sin publicar transcripci?n ni letra: 84 de 86 tokens reconocidos aparecen en el vocabulario de la letra original, y el tramo compartido contiguo m?s largo tiene 43 tokens. Se cuentan 40 marcadores frecuentes castellanos frente a tres ingleses. Esto apunta a una etiqueta de idioma incorrecta aunque el texto coincide ampliamente con la letra castellana. Es una heur?stica, no una transcripci?n de referencia temporizada ni WER; no demuestra exactitud de cada palabra o tiempo. El par?metro expl?cito Spanish sigue pendiente de contraste real y debe constar en el recibo cuando se use.
