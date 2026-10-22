# T09 transition-fix2 — DONE_WITH_CONCERNS

Entrega parcial: conservación del RAW nativo ante fallos posteriores. **R09-T01 y R09-T02 siguen abiertos; O2/v3 no está implementado.** No considerar corregida la transición ni avanzar a QA/GPU con esta entrega.

`benchmark_windows.py` conserva el resultado parcial y su causa mediante `IncompleteWindowsSample`. Guarda cada contador RAW inmediatamente después de retornar PDH, antes de consultar metadatos. `benchmark_observers.py` conserva esos valores con `status=incomplete_invalid` y el error del sensor. No convierte el fallo en un original válido.

Dos regresiones con DXGI/LUID/PDH/ctypes reales pasan: fallo posterior de reloj y fallo de metadatos después de obtener el RAW. La propagación mantiene los contadores y el estado inválido. Las queries se cierran en `finally`; no hay inferencia, CUDA, UI, Docker ni servicios tocados. `native-final.log` contiene los valores originales; no acredita proveedor aislado, navegador ni calibración.

Cinco RED sustantivos siguen fallando: proceso CPU bloqueado **2,2519933 s**; validación **2,2060872 s**, publicación **2,2051555 s** y continuidad **2,2048214 s** aceptadas tardíamente; preparación sintética bloqueada realmente **3,0004383 s** rechazada por cadencia antes de inferencia. El test de preparación comprueba cleanup, restauración del doble Ollama y lease liberado en `finally`. Los sensores y relojes de estos episodios son fixtures explícitas, no medidas GPU.

La ejecución conjunta final y su salida están en `complete-neighbors-native.log`, con cobertura oficial de ambos módulos completos en `coverage-complete.json`, sin exclusiones. Incluye 300 casos vecinos y 2 nativos; excluye explícitamente los cinco RED nuevos. Ruff check/format conformes. No hay suite global verde mientras continúen los cinco RED.

Pendiente R09-T01: proveedor persistente aislado, Job Object sin carrera, PID/creationtime/membership y terminación de descendientes; consultas y RAW parcial bajo deadline original; preparación/publicación v3 con finalización real verificable y validador offline. Pendiente R09-T02: coordinador único durante todo create/start/health/verificación/hash/copia y demás lifecycle, recuperaciones de ack tardío/incierto sin duplicados, integración CLI/runner/calibración/resume/cierre/pilot/builder. No se cambiaron política histórica ni umbrales.

Custodia: 71 protegidos iguales, todas las preimágenes exactas; solo dos módulos existentes cambiados y un test nuevo. No se congelan ni se reclaman intactos los cambios paralelos T02. Los originales fix1 no se modificaron.

Incidentes conservados: primer RED de proceso falló por `last_raw` omitido en el fixture; corregido y reproducido aparte. Primera preparación falló por FILETIME sintético fraccionario; corregida aparte. Dos ejecuciones de vecinos fallaron por rutas relativas al copiar tests: 12 errores de importación y después 3 rutas upstream; solo se corrigieron las rutas del arnés privado. La ejecución inicial usó el `tmp_path` del repositorio y creó temporales sintéticos en `.cache/pytest-tmp`, fuera del privado solicitado; se conservaron, y las posteriores usan rutas privadas. Primeros RED sin brackets UTC del comando; sus logs/JUnit se conservan, los comandos finales sí registran UTC. El RED final tiene un aviso de caché WinError5, con assertions/JUnit completados. El primer intento de generar el recibo falló al parsear el script, antes de escribirlo; corregido después.

Modelo/facturación desconocidos. Atribución proporcional estimada del agregado root: T02 normal5 + T09 fix3, sin medidor individual. Sin Git/ledger/documentación canónica/knowledge/globalmemory ni aceptación QA/GPU/tarea. Root finaliza y sella el CLI terminal; se excluyen los CLI vivos de los sellos de esta entrega.
