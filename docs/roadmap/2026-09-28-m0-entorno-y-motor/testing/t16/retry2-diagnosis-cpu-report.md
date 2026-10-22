# T-16 — diagnóstico CPU y propuesta de instrumentación

2026-10-06. `custom-agents:debug-root-cause`, fases1–3 parciales. La causa del fallo real de90s sigue sin probarse. [Recibo de comprobaciones](retry2-diagnosis-cpu-receipt.json) y [fallo real](retry2-failure-report.md).

La prueba controlada CPU en la imagen exacta9e4fc86 recorre el servicio upstream real con cómputo doble y provoca un ValueError sintético. El proveedor conserva error/traceback, pero el adaptador devuelve INTERNAL constante y no persiste la captura parcial. La limpieza del server elimina la salida fallida. Se prueba pérdida de diagnóstico, no que ese ValueError sea el fallo real ni que exista OOM. El mensaje público estable conserva privacidad por diseño.

Root detectó que la primera propuesta sólo parcheaba el padre: el supervisor inicia otro intérprete que importa el adaptador. Se corrigió exclusivamente la instrumentación privada, manteniendo descriptor, opciones y preflight originales, con una factoría ligera y módulo importable por el hijo. Se preservan la propuesta y validación directa anteriores como antecedentes limitados.

Prueba CPU HTTP TestClient real → server/supervisor/worker reales → adaptador privado derivado en otroPID: exit0, HTTP202, terminalerror, padre sinTorch y trazas conservadas fuera del tmp que limpia el server. Cómputo/preflight dobles declarados; sin pesos, GPU, red del contenedor ni cambios de producto. Root verificó29SHA de archivos congelados; no publica trazas, capturas de entrada, letras, tokens ni entorno.

Propuesta pendiente de revisión: una tomaSFT30s, seed1,50pasos/CFG7/shift1/BF16, misma imagen/LM/entradas de control. Guardas y cleanup proceden del arnés revisado y fijado porSHA; baseline≤1600/Ollama vacío, servicio anterior descargado, contenedor propio y puerto separado. Instrumentación escribe errores/capturas únicamente en caché privada fuera de data/tmp. No hace build ni altera producto/imagen/runner de seis tomas. Todavía no se ejecutó con GPU.

Cambiar90s a30s permite localizar un fallo a menor coste, pero modifica duración y reservaLM: un éxito no refuta el fallo original. Después de leer el trace técnico privado se decidirá si hace falta90s de una sola toma. Ningún resultado diagnóstico aprueba calidad, la comparación de seis tomas, T-16 o M0. No cambiar producto sin hipótesis causal probada y regresión RED. Consumo individual desconocido; comparte las ventanas T08, sin duplicar imputación.
