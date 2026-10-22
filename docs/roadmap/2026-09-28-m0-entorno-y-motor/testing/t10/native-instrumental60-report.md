# T-10 — primera toma instrumental real de 60 segundos

**Generación técnica correcta; aceptación musical pendiente.** Nueva sesión y job propios del plan de522filas; Turbo/LM0.6/BF16/8steps/seed101. [Recibo](native-instrumental60-receipt.json). WAV FLOAT/48kHz/estéreo/2.880.000frames/60s. Raw, copia y PCM pre_splice idénticos. QA independiente48/48 sin fallos, errores ni omisiones.

El LM y el DiT reciben exactamente el caption instrumental sellado y `[Instrumental]`, sin heredar el caption con lead vocals de la canción. LM89tokens+310reserva; captionDiT90/256 y letra15/2048. Controles efectivos corroborados y reescrituras Cot desactivadas. Fidelidad de entrada demuestra transporte, no ausencia acústica de voces ni cumplimiento musical por sí sola.

Las5.760.000muestras son finitas. Una muestra fullscale en frame510633/canal1 (10,6381875s), ninguna por encima de1. La observación estricta de cero fullscale es falsa y no se usa como puerta de producto. El validador canónico pasa su criterio de clipping sostenido:1/5.760.000 muy inferior a0,005. Post canónico conserva WAV y masterFLAC24 sin normalizar, MP3 a−14,025LUFS/−1,2dBTP con limitador y picos. Calidad, presencia de voces y naturalidad requieren escucha.

## Contraste del panel GPU

Captura adicional autorizada guardada durante la generación a21:32:15,356–,609UTC. Esta vez muestra el panel correcto RTX5070:1,3/12GBdedicada y0,1/15,8GBcompartida. La muestra del sensor a21:32:15,569992UTC (0,213992s del inicio de captura) daNVML8904MiB/PDHdedicada8918,34MiB/compartida223,60MiB. **No coinciden:** la calibraciónT09 permanece pendiente; no se atribuye causa ni se certifica ausencia de uso de RAM. No se hacen más capturas fuera de la autorización.

El proceso hijo terminó, VRAM libre recuperada, contenedor propio eliminado y lock liberado. Ollama estaba vacío y se conservó. Guardas no activadas,126muestras NVML/PDH registradas. Fuentes59, helpers y entradas selladas conservados. T-09 y T-10 siguen abiertas; ninguna capacidad se marca verified por esta toma.
