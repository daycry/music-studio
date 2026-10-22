# Cinco tomas default por /v1

Cinco ejecuciones reales, secuenciales y sin reintentos: dos canciones y tres instrumentales de 60 segundos. Modelo Turbo BF16, LM 0.6B, ocho pasos. Todas terminaron sin errores y descargaron el proceso; root cotejó salidas crudas y copias.

| Tarea | Semilla | Pico NVML (MiB) | Muestras de telemetría |
|---|---:|---:|---:|
| music.song | 102 | 9738.0 | 145 |
| music.song | 103 | 9739.0 | 143 |
| music.instrumental | 101 | 9427.0 | 144 |
| music.instrumental | 102 | 9427.0 | 145 |
| music.instrumental | 103 | 9047.0 | 144 |

La recepción de prompts y parámetros no acredita su cumplimiento musical. La QA de muestras PCM e inputs y la valoración musical permanecen pendientes. T-10 sigue abierta. [Recibo](v1-defaults-gpu-receipt.json).
