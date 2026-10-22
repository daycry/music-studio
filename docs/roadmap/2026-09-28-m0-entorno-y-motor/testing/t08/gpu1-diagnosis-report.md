# T-08 — causa CLAP reproducida y diagnóstico ASR pendiente

2026-10-06. Se aplica custom-agents:debug-root-cause tras la [primera integración GPU fallida](gpu1-failure-report.md). [Recibo](gpu1-diagnosis-receipt.json). Worker fresco, CPU únicamente; 20 fuentes de producto y 76 artefactos privados verificados por SHA antes de cambiar producto. TDD n/a: este informe es documentación de la investigación.

Hipótesis probada: el backend fuerza `truncation="fusion"`, que produce cuatro canales, para un checkpoint con `audio_config.enable_fusion=False` cuya proyección espera uno. Para audio sintético de 1 s y 30 s, `LocalBackend.run` real, extractor/tokenizer locales reales y prefijo BF16 real (BatchNorm, reshape y ClapAudioPatchEmbed) fallan: Conv2d `[128,1,4,4]` recibe `[1,4,256,256]`. Cambiar únicamente la estrategia al `rand_trunc` declarado por el extractor permite superar esa proyección en ambos casos. No se cargaron pesos ni se ejecutaron las capas posteriores: no acredita scoring completo ni todas las causas GPU.

Corregir la estrategia conforme al checkpoint, sin modificar arquitectura, pesos o activar fusión ficticia. La regresión deberá alcanzar la proyección real; el doble de embeddings usado anteriormente no detectaba esta incompatibilidad. Mantener texto completo y declarar la ventana efectiva de audio. Esta fase nueva responde a evidencia de integración posterior a revisión3/QA CPU; no reinicia ni oculta sus tres intentos anteriores.

ASR no tiene causa probada. Su error seq3 ocurre antes de `loading_aligner`, entre transcripción y validación de texto/idioma. Se preparó instrumentación privada importable en el hijo y runner de un trabajo, validando HTTP→supervisor→worker con cuatro casos de cómputo doble CPU, errores y cleanup reales del transporte. No se ejecutó ASR GPU desde el worker. La propuesta requiere revisión independiente y preflight antes de ejecutar; no se publica traceback, audio ni transcripción.

T08/M0 siguen abiertos, sin calidad aprobada. Fuentes y pesos intactos; conocimientos ajenos preservados. No se imputa consumo individual a tareas concurrentes.

