> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Corrección de formato QA01

Sólo Ruff modificó test_worker_native_linux_custody.py. AST completo idéntico con type_comments=True y comentarios idénticos. Los siete restantes del alcance Ruff y las fuentes protegidas permanecen byteexact.

TDD n/a: ajuste estático de layout; sin RED causal inventado.

Ruff check --no-cache y Ruff format --no-cache --check sobre los ocho ficheros originales: exit 0; argv, PID, wait, UTC, stdout y stderr en los recibos de comandos. Diff original QA01 preservado como qa01-original-ruff-format-stdout.txt.

Sin nueva ejecución native88, suite o cobertura. Producción permanece idéntica; evidencia anterior QA01 referenciada sin modificar ni unir RAW. Root conserva revisión fresca, suplemento QA independiente y aceptación.

Intérprete y Ruff capturados antes de Python; límites físicos/TCB/transitorios declarados en receipt.json. Métricas de modelo, tokens, EUR y horas: null.

Comparación histórica: queue/events.py y sse.py ya diferían de QA01 al capturar esta fase; ambos quedaron byteexact antes/después. Las cuatro fuentes runtime de custodia coinciden con QA01. No se atribuyen los cambios disjuntos a esta corrección.

Incidente de captura: primer intento PowerShell falló antes de Python/formatter por ausencia de IO.Path.GetRelativePath en este shell; se corrigió sólo el cálculo privado de rutas. El intento de crear el directorio privado encontró que ya existía; no se eliminaron archivos. Historial real disponible en la conversación. No son RED de producto.
