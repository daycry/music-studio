# Corrección T-10 — firma de las capturas temporales

R10-08 corregido: las funciones que envuelven métodos temporales conservan metadatos y firma mediante `functools.wraps`. El proxy tokenizer conserva su comportamiento como objeto invocable. [Recibo](fix3-receipt.json).

RED propio: el filtro basado en `inspect.signature` descartaba `captions` y provocaba TypeError. La regresión ahora preserva parámetros y firma y comprueba restauración normal y tras excepción. La sonda CPU con el generador realmente instalado en la imagen sellada confirma firmas iguales, `captions` presente, parámetros conservados y resultado igual al control sin captura. Ambos llegan a la guarda de modelo no inicializado, esperada sin cargar pesos.

Una suite ampliada: **91 pruebas pasan en 6,13 s**, sin fallos ni omisiones. Cobertura oficial del único archivo de producción modificado **307/346 = 88,7283 %**. Ruff y formato conformes en los dos archivos. Root verifica las 59 fuentes, artefactos y JUnit; 57 fuentes ajenas se conservan. Contenedor CPU propio eliminado, CUDA sin inicializar, sin pesos ni GPU.

La primera excepción histórica de GPU sigue sin identificarse: la prueba demuestra el defecto del DiT, no que fuera el primero de aquella toma. Revisión, QA y nueva ejecución GPU con diagnóstico privado siguen pendientes. No se cambia política de errores públicos, entradas, semillas ni capacidades verificadas. T-10 permanece abierta.
