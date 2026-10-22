# Generación real de canción de 60 s por /v1

La API del contenedor entrega un WAV crudo y su recibo de entrada. Root cotejó los originales con las copias por SHA-256, los eventos y los cinco registros LM/DiT. La QA independiente de muestras y condicionamiento está pendiente.

Sesión `t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa`, job `01M49JY83KY4PDQ96RTWYWEMJZ`; Turbo, LM0.6, BF16/PT, seed101 y 8 pasos. Inferencia CUDA sincronizada: 22.579957 s, excluye carga y postproceso. Una sola medición no permite un ranking de rendimiento.

Telemetría: 151 muestras; NVML inicial 1269 MiB y máximo 9432 MiB; PDH compartida máxima 216.59 MiB. No se activaron guardas. No certifica cero desbordamiento ni resuelve la calibración pendiente de T-09.

Proceso hijo terminado, contenedor propio eliminado, lease liberado y VRAM recuperada. Ollama inicialmente vacío se conserva vacío; fuentes59, protegidos32 y originales15 intactos. No se usó control de pantalla ni capturas.

Aceptación musical, cumplimiento acústico, resto de la matriz y T-10 permanecen pendientes; `verified=false`. [Recibo técnico](v1-song60-receipt.json).
