# T-16 — corrección CPU del arnés

Fecha: 2026-10-06. Corrige los cuatro Important de [la revisión del arnés](harness-review-1.md), conservando el producto y la imagen CPU ya aprobados. Orquestación privada en .cache/dev-cycle/t16; TDD n/a para código efímero. Se escribieron regresiones antes de corregir y se ejecutaron sobre AST/fragmentos del arnés real, no sobre una reimplementación.

## Resultado

- El arranque entra en el bloque protegido por finally. Cada contenedor nuevo recibe etiqueta de sesión/configuración. La limpieza verifica etiqueta e imagen y usa el ID capturado, nunca detiene un contenedor coincidente solo por nombre.
- Un timeout de logs no impide stop/rm; un timeout de stop permite rm --force únicamente del ID propio verificado. Si Docker no permite verificar identidad o quitarlo, la ejecución falla y no registra una comparación terminada.
- Un job ajeno detectado por el monitor o por la lectura final conserva su contenedor y deja cleanup diferido en el registro privado. La ejecución se aborta sin lanzar la configuración siguiente; no se declara descarga. La comprobación final no promete una transacción de exclusión frente a clientes concurrentes ni permite inferir identidad cuando el endpoint no responde.
- La referencia se copia a temporal exclusivo, se verifica y se publica por hardlink atómico sin sobrescritura. Una interrupción anterior a publicación deja libre el nombre final; el original se conserva. Un temporal o destino ajeno preexistente no se elimina ni reemplaza.
- El empaquetador importa math para la validación MP3 heredada de T-15.

## Evidencia

Comando RED, ejecutado antes de modificar runner/packer: `uv run --frozen --all-packages pytest .cache/dev-cycle/t16/test_harness_fix1.py -q -p no:cacheprovider --basetemp .cache/dev-cycle/t16/pytest-harness-red` → exit1, siete fallos esperados: dos OWNED_STOP_NOT_ATTEMPTED, OWNED_REMOVE_NOT_ATTEMPTED, dos FOREIGN_JOB_KILLED_INDIRECTLY, PARTIAL_FINAL_REFERENCE_PUBLISHED y NameError math. Un aviso por cache_dir con cacheprovider desactivado; no afecta a los fallos reproducidos.

Primer GREEN → siete casos verdes. Regresiones adicionales sobre etiqueta/imagen ajenas, destino/temporal ajenos y FFprobe real de una senoide existente de90s → **12 passed**, exit0, sin avisos en la ejecución root. Comando final: `uv run --frozen --all-packages pytest .cache/dev-cycle/t16/test_harness_fix1.py -q -o cache_dir=.cache/dev-cycle/t16/pytest-cache-harness --basetemp .cache/dev-cycle/t16/pytest-harness-green2`.

`run-comparison.py --prepare-only` → ready_cpu, seis tomas previstas, exit0, gpu_executed=false. AST3.11 de cuatro archivos conforme. [Recibo con hashes antes/después](harness-fix1-receipt.json). Los recibos guards-cpu-receipt.json y packer-cpu-receipt.json anteriores se preservan como antecedentes de sus versiones; no prueban las fuentes corregidas ni se sobrescriben.

Docker es doble CPU; el único audio leído para FFprobe es la senoide existente de las pruebas anteriores. No se ha generado una canción, empaquetado los seis audios reales ni aprobado su calidad. Los tests no acreditan que Docker real limpie o que la GPU respete el presupuesto. Segunda revisión y QA independiente tienen recibos separados.

Ventana de corrección00:22:14–00:26:14 UTC, fuente estimado; tiempo IA, tokens y coste reales null. Sin cambios de dependencias, pesos, locks, contratos, código de producto ni imagen. T-16 en-progreso, CA3/4 abiertas; GPU sigue condicionada a AGENTS§4.8 o autorización nueva expresa.
