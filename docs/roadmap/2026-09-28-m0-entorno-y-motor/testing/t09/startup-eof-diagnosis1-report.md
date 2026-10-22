> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Diagnóstico privado de EOF — parcial, original no resuelto

OWNED producto: []. Sólo salida en startup-eof-diagnosis1. No aceptación, ledger, documentación, ADR, Git, objetivos o conocimiento. Sin subagentes. Fases 1–3 de debug-root-cause; fase 3 de producto NO probada. TDD n/a: diagnóstico readonly; ningún error de importación se declara RED causal de producto.

## Evidencia y límite de reproducción

El original final03 sigue sellado: 300 casos, 269 PASS, 1 FAIL y 30 errores de fixture; 26 nuevos PASS. Los 30 mensajes efectivamente dicen fixture harness_module ausente. La única falla funcional original llega en consume_runtime/read base con worker_pipe_eof; stderr original DEVNULL. No se recuperó ni inventó stderr histórico. WHOLE71.93 del coordinador procede de traza fallida, no acredita 80 ni U1.

Se copió con igualdad byte/AST el archivo entero test_benchmark_canonical_integration.py, sin modificar asserts, parámetros, decoradores, timeouts ni funciones. El harness copiado se registró como diagnosis_harness_unique1. El primer bootstrap terminó antes de Popen nativo por ausencia de test_benchmark_observation en PYTHONPATH: bootstrap-* preserva ese intento (0 nacimientos). Se añadió únicamente la ruta real de tests al entorno privado antes del único caso con nacimiento.

El único caso posterior terminó FAIL durante la primera actual_sensor_factory, antes de crear la sesión y llegar al consume original. JUnit contiene exactamente 1 caso. Hijo real PID 28632, exit 1, espera directa; stderr 237 bytes, todos conservados bajo límite 16384:

```
Traceback (most recent call last):

  File "/.cache\dev-cycle\t09\startup-eof-diagnosis1\native_trace.py", line 6, in <module>

    import coverage

ModuleNotFoundError: No module named 'coverage'
```

Esto prueba únicamente la causa del EOF NUEVO: el wrapper nativo diagnóstico termina por import coverage ausente bajo el intérprete base gestionado. El runner omitió .venv/Lib/site-packages de PYTHONPATH, presente explícitamente en final03/launch.json. Es una divergencia introducida por este actor, no evidencia de defecto productivo/histórico. No se corrigió ni repitió después del primer nacimiento: cuota consumida. No hubo PASS ni reproducción funcional original.

## Aislamiento y hipótesis falsables

La explicación nueva queda acotada a native_trace.py:6, antes de runpy del runtime, gate leído por el hijo, handler y protocolo canónico. El padre sí escribió gate y observó EOF; su revocación era false al finalizar _read y true después de cleanup. No hay llamadas ParentMux ni watchdog registrado porque no se llegó al modo canónico. No se atribuye a carga temporal, latch, epoch o timeout.

H1 producto pendiente: una excepción no transportada de serve_mux/read_steps durante la adquisición concurrente termina el hijo canónico y provoca EOF. El código rechaza read_steps cuando transfer/tentative existen (canonical_head_unpublished) y permite prioridad de ingest entre pasos de lectura; es un candidato concreto, NO una causa confirmada. Falsación mínima: observar stderr real del hijo canónico en el mismo original; una excepción diferente o ausencia de muerte canónica refutaría esa formulación. Ni startup revocation ni inconsistencia epoch/session ni watchdog se confirman o descartan históricamente con este intento.

## Custodia, observación y TCB

Native-results/boundaries/births contienen argv real y original, UTC, handles reales, Job assignment y refs fuertes a Popen/Job/OwnedProcess. Se retuvo como testigo extranjero el propio proceso pytest vivo antes y después; no representa censo ni exclusividad del SO. Cleanup confirma CLOSED_CONFIRMED, Job vacío, ownership original, lector y escritor unidos; hilo stderr unido y sin error; sólo MainThread al final. No numeric/name kills ni limpieza ajena.

El único cambio de transporte deliberado fue stderr DEVNULL→PIPE drenado continuamente por hilo adicional, guardando primeros 16 KiB y contando todo lo drenado. stdin/stdout y Job originales pasantes; gate/frames/model/config sin falsificación. Instrumentación privada de fronteras, máximo 512 registros, contadores en memoria; wrappers pasan resultados/excepciones originales. Se mantuvo la técnica histórica de wrapper coverage y profiler de retornos (no perfilado por línea), cuyos efectos y handle/hilo extra impiden equivalencia temporal y prueba de causa histórica. El argv efectivo usa alias propio de native_trace.py; el argv original del runtime está registrado. La divergencia involuntaria de PYTHONPATH invalida la reproducción funcional, declarada arriba.

Antes de pytest/native Popen: copias físicas de scripts/eval, packages Python, runner/fixtures/harness, intérprete base gestionado/stdlib/DLL, venv y dependencias existentes; hashes y rutas en source-before. Antes de cada nacimiento: fixture/config creados en fixtures copiados y siete fuentes runtime verificadas; actual-runtime-imports prueba rutas reales. Siete runtimes intactos y iguales a final03. Captura secuencial, no snapshot atómico; imports iniciales de stdlib del propio runner ocurren antes de su archivo y no quedan retroacreditados. Alias de módulos, archivos transitorios y clausura universal cargada por SO UNKNOWN; no se concede autoridad por etiquetas JSON. Variables UV/TEMP/TMP/pycache/coverage privadas antes de env.ps1/imports; instalación uv base existente y venv se reutilizan, sin instalación ni descarga. El raw coverage padre es diagnóstico de un caso; no native coverage porque falla su import, sin combine/extracción/unión histórica/gate80.

## Siguiente acción exacta para Root

No se propone parche de producto: no hay causa de producto probada. Proponer una NUEVA autorización de un único probe del mismo nodeid, en namespace nuevo de Root: bootstrap único ya reparado y añadir explícitamente la ruta existente .venv/Lib/site-packages a PYTHONPATH ANTES de importar y de Popen, cotejando contra launch.json original. Preflight estático del entorno/interprete/dependencia y hashes antes de gastar el caso. Mantener stderr acotado, asserts/deadlines/protocolo y custodia sin cambio. Si ese probe confirma excepción concreta de serve_mux, Root despacha TDD fresco con ownership explícito; los módulos canónicos permanecen protegidos, ningún patch autorizado aquí.

Originalfailure sigue honesto y U1 NOaccepted. Este resultado no justifica optimización, redesign, lowering deadlines ni cambios de FIRSTcause.
