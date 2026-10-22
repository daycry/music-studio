# Correcciones CPU del benchmark — fix2

Entrega cotejada por el orquestador: **33 fuentes verificadas**, 32 preimágenes idénticas a fix1 y cuatro archivos cambiados (tres existentes y una nueva batería de regresiones). Los otros 29 archivos de la baseline siguen intactos, incluidos 28 fuera de ownership y el test runner permitido pero sin cambios. [Recibo](fix2-receipt.json). T-09 continúa en-progreso.

Suite: **267 passed, 5 skipped, 1 GPU deselected, 1 warning**, 23,32 s. Cobertura oficial: **87,45 % de media aritmética sobre los mismos 15 módulos de producción**; mínimo individual 67,96 %. No es cobertura de líneas modificadas ni garantía mínima por archivo. Ruff exit0 y comprobación de formato del orquestador: cuatro archivos conformes.

El diagnóstico previo aisló dos causas. El parser chunked hace varias lecturas dentro de read1; con extensión válida tardaba325ms para un plazo40ms. El runner añadía otro segundo de espera después de un sensor500ms, creando muestras en0/1,5/3s. La solución recalcula el presupuesto absoluto en cada lectura socket, además de conexión/envío/cabeceras, y resta el coste del sensor al periodo de observación. Usa la biblioteca estándar y conserva el cierre de conexiones sin hilos supervivientes.

Cinco regresiones se ejecutaron en RED antes de su corrección y luego GREEN: parser chunked, cadencia, terminal tardío, conservación del deadline original en request_before y límite de línea4MiB antes de decodificar aunque tenga newline. La batería incluye HTTPConnection/HTTPResponse reales sobre transporte en memoria, con timeout restante efectivo; no es una ejecución de red o GPU. Los timestamps derivados del archivo de salida se identifican como tales en el recibo.

Fases1–3, controles y preimágenes están archivados en el recibo privado; el diagnóstico y las regresiones constituyen la evidencia de fase4. El implementer reutilizó su contexto después de dos rechazos de contexto fresco por límite de threads; se declara esa limitación. No se escribió gotcha/memoria/conocimiento ajeno. No cambiaron engines, modelos, contratos ni dependencias y no hubo instalaciones, Docker, GPU, audio o sensores reales por el implementer.

R09-04a/b quedan entregados para revisión3de3, no cerrados por adelantado. Se preservan todas las correcciones anteriores y el rebate parcial R09-07. Pendientes revisión independiente, QA sinUI, evidencia GUI, imagen/runtime y matriz de160generaciones. Ningún criterio de calidad musical o benchmark GPU queda acreditado por esta entrega. TDD n/a: publicación de este informe.
