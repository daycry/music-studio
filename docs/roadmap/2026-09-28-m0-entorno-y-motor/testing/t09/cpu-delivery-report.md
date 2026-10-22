# Entrega CPU del benchmark de la RTX 5070

Entrega congelada y cotejada por el orquestador: 32 archivos por SHA-256 y tamaño. Estado CPU_WITH_CONCERNS; T-09 sigue en-progreso. [Recibo](cpu-delivery-receipt.json).

La suite dirigida termina con **223 passed, 5 skipped, 1 deselected, 1 warning** en 22,02 s. El test GPU no se ejecutó. El aviso corresponde a cache_dir con el plugin de caché desactivado. Ruff dirigido: exit 0, All checks passed! La siguiente puerta es revisión independiente y QA.

La cobertura procede del JSON oficial de pytest-cov: **85,33 % de media aritmética de los 15 archivos de producción de T-09**, conforme a la agregación por archivo del plugin. No representa cobertura mínima por archivo ni de líneas modificadas. El mínimo individual es 54,07 % en benchmark_runtime.py; el detalle íntegro está en el recibo. No se usó el diff Git compartido para mezclar tareas previas en el cálculo.

El arnés prepara la matriz de 160 jobs, perfiles explícitos, medición directa, observación NVML/PDH y aislamiento de recursos Docker propios. Los tests de integración CPU utilizan dobles; no acreditan ninguna fila real del benchmark. INT8 se comprueba por versión y por todas las capas Linear esperadas, pero faltan los tensores reales y la prueba de ajuste en VRAM.

Se conservan los RED previos y los GREEN finales. Entre ellos: matriz ausente, aceptación incorrecta de cuantización parcial, terminador REG_MULTI_SZ y alias Perflib. Los dos defectos Windows tienen además [observación nativa de solo lectura](windows-native-probe-report.md); aún falta calibración con Administrador de tareas bajo carga.

El diff de revisión separa seis archivos de producción y los tests existentes contra la imagen anterior recuperada; los archivos nuevos y el cambio único de clasificación del silencio XL se cotejan con HEAD 8663287. Los tests históricos sin cambios se conservan pero no se presentan como implementación nueva. No se modifica el working tree anterior para separar tareas.

Pendiente: revisión A/B/C/D, QA, nueva imagen y compatibilidad efectiva torchao/Torch, prueba INT8/offload, evidencia de navegador visible y calibración Task Manager, preflight y 160 jobs nuevos con medición real bind/copia. Todos los criterios del benchmark siguen abiertos. Esta entrega no decide el motor, la naturalidad vocal ni la fidelidad artística. TDD n/a para este informe y la publicación de recibos.
