> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Corrección acotada B-01/B-02

Estado: DONE_WITH_CONCERNS; entrega para review2 y QA de root. No cierre T05/M1.

B-01 confirmado causalmente: `.owner` fallaba fuera del finally. RED red-lock: dos AssertionError (lock vacío existente) para disco lleno/cancelación, exit 1, UTC/JUnit/fixtures/preimágenes originales conservados. B-02 confirmado: hashes intactos y stat POSIX TESTDOUBLE sin ejecución, check devolvía 0 en ambos binarios; RED red-mode exit 1. Comandos y fechas exactas: sus command.json.

Fix mínimo: arranque/marcado del lock dentro del finally; limpieza del vacío sólo con identidad acreditada, y del marcado sólo con token y entrada única. Custodia UNKNOWN conserva. Stage con token conserva su cleanup independiente. Linux exige los tres bits X normalizados sólo para bin/ffmpeg y bin/ffprobe; Windows no infiere corrupción por X ausentes.

GREEN regresiones: 13 PASS/45 deselected. Final única traza actual: 58 PASS, módulo entero 334/379 = 88.12665 %, cero exclusiones. Funciones antiguas AST idénticas: 25. Fuente final coincide SHA con preexecution de final-baseline. No unión de trazas.

Carga oficial existente: --check Windows exit 0; todos los archivos SHA/tamaño antes/después iguales. No red ni ejecución de binarios. Linux nativo UNTESTED. Las identidades mutadas y modos son TESTDOUBLE, no pruebas nativas Linux. Limitación TOCTOU concurrente universal UNKNOWN.

Delta protegido concurrente: []. No cambios fuera de ownership por este actor. Métricas reales modelo/tokens/EUR/horas IA NULL.

Custodia documental: tests/fixtures definidos en test y runner copiados antes de cada run. Helper test_workspace y config copiados aparte antes de final, pero faltan copias independientes por RED; no reconstruidas después. Inventario NONCLI excluye sólo cuatro ficheros reservados de primer nivel y su propio inventario. Root conserva ledger/docs/Git/acceptance/meter.

DONE_WITH_CONCERNS: Linux nativo pendiente y copia independiente del helper por RED ausente; review2/QA root pendientes.
