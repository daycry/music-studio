# Corrección de observación con sensor lento — fix3

Entrega cotejada: **33 fuentes y 33 preimágenes verificadas** por SHA/tamaño. Sólo cambiaron el runner y sus regresiones de deadline; otros31archivos siguen intactos. Esto incluye30archivos fuera del permiso de escritura y el test runner permitido pero sin cambios. [Recibo](fix3-receipt.json). T-09 permanece en-progreso.

Suite: **272 passed, 5 skipped, 1 GPU deselected, 1 warning**, 24.64s. Cobertura oficial: **87,55% de media aritmética sobre los mismos15módulos de producción**, mínimo67,96%; no porcentaje de líneas modificadas ni mínimo por archivo. Ruff/formato del alcance exit0; GREEN dirigido55tests.

El diagnóstico reprodujo la inanición con sensor1,5s: ningún canal del engine se consultaba aunque done estuviera disponible. Un RED propio falló con ObservationTimeout antes del cambio. Ahora, si se agota el periodo pero queda horizonte global, el engine tiene una oportunidad acotada de observación. Eventos y estado comparten un deadline; no se conceden dos periodos independientes. El caso sensor500ms conserva presupuesto500ms y muestras0/1/2/3s.

Regresiones adicionales cubren coste igual al periodo, progreso/seq/after, consulta de estado y reanudación del mismojob, terminal tardío y sensor que agota el horizonte. Para un sensor lento se conserva la cadencia observada degradada: no se promete1s exacto ni se vuelve invisible el trabajo. El transporte HTTP anterior no cambió y conserva sus pruebas.

Diagnóstico, RED/GREEN y artefactos sellados pasan a revisión4; no se cierra R09-08 por adelantado. Root eligió esta continuación bajo la delegación vigente del propietario; intentos1/2/3 se conservan, sin reset. Pendientes revisión, QA sinUI y benchmark real. No GPU, Docker, red, pesos, sensores reales, audio, memoria o conocimiento ajeno. Computer Use continúa detenido trasEscape. TDDn/a: publicación del informe.
