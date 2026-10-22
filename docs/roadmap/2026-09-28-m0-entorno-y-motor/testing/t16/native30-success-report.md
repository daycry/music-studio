# T-16 — prueba SFT real tras resolver la rama nativa del DiT

2026-10-06. **Una toma real de 30 s completada**, exec75371 exit 0; CLI 181.38 s de reloj, unload confirmado y sin motivo de parada. Imagen inmutable `18d94fd…`. [Recibo](native30-success-receipt.json).

El upstream resuelve internamente text2music → cover cuando el LM produce códigos de audio. El recibo v2 selecciona esa rama: **150 tokens DiT previstos y 150 capturados**, 256 tokens de letra, instrucciones y SHA coincidentes. LM condicional397/incondicional33 y reserva160 se capturan; metadata BPM94/duración30/idiomaes. La corrección elimina el fallo real previo de «Tokens DiT cambiaron tras el preflight» y llega a generar audio con el transporte nativo intacto.

Controles reales: SFT50 pasos, CFG7, shift1, seed1, BF16. WAV crudo FLOAT a48kHz, dos canales, 1.440.000 frames/30s exactos, todo finito, RMS0.18725882. Master FLAC/MP3/peaks/manifiesto publicados en `data/cli/2026-10-06/01M47NPBCBBRBG9V3GVAD4JAEF/`; `verify_manifest.py` → all valid (1 manifests), exit0. La toma y los recibos son nuevos; originales y generaciones previas se conservan.

Pico VRAM7807.94MiB, cap10117.13MiB, spilled=false; GPU después1314MiB y contenedor propio retirado. 74 muestras WSL: pico usado excluyendo disponible4763,93MiB y swap6,04MiB. `load_s`124,26 y `run_s`162,42; run incluye carga, RTFnull, no se suman relojes ni se llama inferencia pura a su diferencia.

Las nueve fuentes productivas siguen congeladas. Revisión de producto A+B+C y QA314/64de68coverage; nuevo harness revisión A+B+C+D y QA14 acreditados antes de cargar GPU. Traces y captura privadas fuera de TMP en `.cache/dev-cycle/t16/native-resolution-gpu-runtime/01M47NPBCA685GPK5W1XQQEKCY/`. No se publican letra, caption, tokens reversibles ni códigos de audio.

El mensaje de progreso «Grupo1/2» procede del supervisor reutilizado; la reserva, petición y manifiesto corresponden a una sola toma de30s. **Esta prueba no acredita las seis tomas de90s ni su calidad musical.** CA3/4 permanecen abiertas. Siguiente paso: derivar el harness de comparación con la imagen nueva, revisar/QA y ejecutar seis tomas nuevas Turbo/SFT bajo transporte actual, antes de la escucha.
