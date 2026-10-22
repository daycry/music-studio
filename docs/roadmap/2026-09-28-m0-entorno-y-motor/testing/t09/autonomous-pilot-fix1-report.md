# Corrección privada de custodia del piloto T-09

Estado: **DONE_CPU_READY_FOR_REVIEW**. Sólo cambia el ejecutor privado `.cache/dev-cycle/t09/autonomous-pilot-root.py`; producto, documentación, ledger, Git, modelos y datos reales no se modifican. Requiere revisión y QA independientes antes del piloto real.

Los cuatro fallos B4-L01–04 se reprodujeron antes de cambiar el script: cada prueba importó y ejecutó `run()` del archivo real completo con hardware/transporte/E/S simulados. Preimagen SHA `bfe6ee8ff04990619a78b289b219035b865328e0de8f60d7e2bc1fec66466ca9` en `pilot-before.py`.

| Gap | RED propio original | Resultado original |
|---|---|---|
| B4-L01 | `test_snapshot_failure_releases_unmutated_lease` | AssertionError: lease sin liberar |
| B4-L02 | `test_failure_receipt_io_does_not_block_cleanup` | AssertionError: recurso sin eliminar |
| B4-L03 | `test_container_receipt_io_cleans_acknowledged_created_resource` | AssertionError: recurso conocido sin eliminar |
| B4-L04 | `test_cleanup_receipt_io_never_repeats_completed_cleanup` | AssertionError: lista de modelos sin restaurar |

Los logs `red-<test>.txt` y sus `red-<test>-metadata.json` conservan argv, UTC inicial/final y exit1 originales. `green-gaps.txt` muestra `4 passed, 1 warning`; el aviso se debió a desactivar cacheprovider frente a la configuración heredada. Las pruebas finales usan `pytest.ini` privado.

La región de recuperación comienza antes de adquirir el lease y toma decisiones según reconocimientos de recursos, independientemente de la persistencia de recibos. El estado de contenedor se borra en memoria inmediatamente después de un cleanup confirmado, antes de escribirlo. El contenedor conocido aún sin API se limpia mediante la primitiva existente, que comprueba propiedad y procesos muertos. Los errores secundarios se propagan junto al error original mediante ExceptionGroup, nunca se silencian.

Sólo se cancela el job propio. La restauración usa la lista original y verifica el estado actual: sin descarga iniciada, no recarga; lista original intacta, no recarga; estado vacío tras descarga, restaura mediante la primitiva existente. Un estado parcial/ajeno o creación/cleanup inciertos mantiene el lease y reporta el error. No se libera la exclusión ni se recargan modelos sobre recursos inciertos. Ollama originalmente vacío conserva una lista vacía.

La sanidad ejecuta también el cleanup de producción sin modificarlo, con `inspect` y comandos Docker simulados; ningún proceso, red, Docker, WSL, GPU o servicio real se usa. La ruta simulada completa conserva solicitud `music.instrumental` de 60 s fuera de matriz 160, los 30 originales (10 baseline + 10 loaded + 10 unloaded), contexto adquirido antes de cada prueba de salud y referencias SHA reales de los archivos privados. No relaja las validaciones de producto.

Comprobación final única (`cpu-final-metadata.json`): **27 passed in 0.60s**, exit0. Cobertura oficial `coverage.json`: **170/184 líneas, 92,3913043478261%** del archivo completo del laboratorio, sin exclusiones; CLI real prepare/run no se ejecutó. `junit.xml` contiene 27 casos. Ruff final: `All checks passed!`; formato final: `2 files already formatted` (ambos exit0, target Python 3.12 explícito para lint).

Incidentes preservados: `green-safety.txt` tuvo cuatro fallos de fixtures adicionales (job activo antes del arranque y funciones reemplazadas sin self); se corrigieron, no son RED TDD. `ruff-check.txt` tuvo errores iniciales de orden de imports, estilo/captura de errores y target Python no declarado; `ruff-check-final.txt` tuvo después un error UTC. Todos los logs y metadatos se conservan; no se reconstruyen argv ni fechas originales. Las capturas amplias de excepciones recuperables están anotadas puntualmente porque se propagan en el grupo final.

`sources-after.json` y `t20-docs-after.json` comparan las 64 fuentes y 12 documentos contra freezes originales. `root-coverage-proof.json` verifica `.coverage` raíz contra el SHA observado antes de editar. `pilot-after.py` conserva la entrega; `receipt.json` (schema_version 1) resume resultados y checks; `artifact-seals.json` (schema_version 1, files[path]={bytes,sha256}) sella los archivos de evidencia superiores y el script vigente. Tmp/cache privados se excluyen explícitamente del inventario estable.

No hay acreditación CUDA/GPU, calibración, resultado musical, ejecución real de piloto ni terminación de T-09/M0. Ledger y medición corresponden exclusivamente al orquestador.


Root cotejó sellos y resultado final. [Recibo](autonomous-pilot-fix1-receipt.json).
