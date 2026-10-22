# T-10 — primera ejecución native song60 con GPU

**Falla con INTERNAL y no produce WAV.** La toma pertenece a la matriz íntegra de T-10, perfil Turbo/LM0.6/BF16/8 pasos, semilla 101 y texto original del laboratorio. [Recibo](native-song60-first-receipt.json).

Ollama estaba vacío; baseline NVML bajo 1.600 MiB. Se adquirió el lock GPU, se lanzó únicamente un contenedor propio y el proceso hijo cargó el modelo. La generación devuelve un error genérico del adapter; ese mensaje por sí solo no identifica la causa. No se declara inferencia ni aceptación musical correctas, ni se repite la toma sin diagnóstico.

Telemetría real: 125 muestras, máximo NVML 9027.00 MiB, memoria dedicada PDH 9041.06 MiB y compartida PDH 211.97 MiB frente a baseline 127.24 MiB. No se activó la guarda de crecimiento compartido ni la de VRAM libre. Son sensores y guardas operativas; falta contraste Task Manager bajo carga y esto no certifica ausencia de desbordamiento para T-09.

Cleanup verificado: el hijo termina, memoria libre vuelve a su baseline dentro de tolerancia, contenedor propio eliminado y lock liberado. Ollama sigue sin modelos cargados; no se descargó ni se restauró ningún modelo ajeno. 59 fuentes, lock, texto y `.coverage` preservados. La ventana de medición queda cerrada, estimado/null sin atribuir coste real.

Siguiente paso: reproducción e aislamiento en CPU con las interfaces reales del upstream sellado, antes de otra carga GPU. No alterar la política de errores públicos ni la imagen para obtener un falso verde. T-10 y M0 siguen abiertas.
