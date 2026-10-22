# T-10 — song60 generada y entrada efectiva auditada

**La segunda toma genera un WAV real de 60 s, estéreo FLOAT a 48 kHz.** Raw, copia y PCM capturado coinciden; las 5.760.000 muestras son finitas. [Recibo](native-song60-second-receipt.json). No se declara aceptación musical ni capacidad verificada.

La letra original, con tildes y etiquetas, y el style llegan exactamente al LM y al DiT. Capturas reales: LM 198 tokens + 310 de reserva, dentro de 4096; DiT style 94/256 y letra 120/2048. Semilla101, Turbo8, LM0.6, BF16/PT, thinking true/CFG2, sin reescritura Cot de caption/metadatos/idioma. Tiempo de una llamada sincronizada CUDA: 22,9289 s; no es el benchmark de 160 ejecuciones ni una comparación de calidad.

QA independiente conserva **40/41 comprobaciones y un fallo estricto**: exactamente una muestra llega a −1, en 54,330583 s; ninguna excede 1 y no hay mesetas consecutivas. No se oculta el JUnit rojo ni se certifica ausencia de clipping. El validador canónico de audio del proyecto sí pasa: la fracción a fullscale es 1/5.760.000, por debajo del umbral de clipping sostenido 0,005. Esta diferencia de criterio queda documentada, sin modificar el raw.

El postproceso canónico produce master FLAC24 sin normalizar, MP3 de escucha y picos. MP3 medido −14,0005 LUFS y −1,3 dBTP; se aplicó limitador y se registra. El raw permanece intacto. El recibo derivado del driver leyó UTF-8 como cp1252 y tiene mojibake; las fuentes de verdad son los JSON nativos UTF-8 intactos, no esa copia de metadatos.

126 muestras de telemetría: máximo NVML9747 MiB, PDH dedicada9761,14/compartida224,40 MiB. Modelo descargado, memoria recuperada, contenedor propio eliminado y lock liberado; Ollama permaneció vacío. No se activaron guardas. La captura de Task Manager devolvió una imagen ajena al panel y no se guardó: T-09 sigue sin contraste representativo. El propietario ha dejado el panel en primer plano para la próxima prueba; no se fabrican valores ni calibración.

59 fuentes y protegidos intactos. T-10 continúa abierta con la matriz completa de 522 casos; sólo esta fila tiene una ejecución musical registrada. Sigue pendiente escuchar naturalidad, afinación, ritmo e instrumentos y cumplir las capacidades restantes. El éxito corrobora la corrección de captura sin establecer la primera excepción histórica como causa única.
