> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# FC02: causa primaria dentro de la ingesta canónica

Cambio mínimo en los dos ficheros asignados. Los manejadores de `ingest_latest` y `_ingest_latest` conservan la primaria con `raise`: fallback secundario tipado/acotado, digest y reloj UNKNOWN antes del logger seguro, y guarda exterior contra fallos de registro o metadata. No usa mensajes secretos ni `__str__`. La propiedad fuerte del worker/Job/proceso/reader permanece en los objetos originales; abort incompleto sigue UNKNOWN_QUARANTINED. Cierre sin primaria conserva su propagación anterior: no cambia `close`, `abort_owned` ni `_cleanup`.

Dos RED causales nativos previos al cambio, exit 1: `record-observation` llega a la línea original 1059; `record-begin` llega a 1142. En ambos, OSError del registrador sustituye PrimaryFailure antes de que Episode registre interrupción. Ver `causal-red-proof.json`, JUnit y capturas antes del rescate. La primera primaria nace dentro de `_ingest_latest`, después de evidence real del Job del sensor; la segunda después del begin real sobre el gate/backend, sin ingesta exitosa previa ni publicación. No se simulan procesos/kernel ni certificados booleanos. Fallos CONTROLADOS; no avería espontánea del SO. La prueba AST anterior permanece STATIC, no RED nativo.

GREEN: ocho parámetros pasan para ambas ramas y modos none/record/safe_record/storage. Identidad/tipo/nodo traceback, interrupción en memoria, cierre del sensor, ausencia de head/recibo/posición positivos y testigo extranjero intacto se comprueban antes de rescatar las referencias originales. No persistencia durable inventada, retry de efectos ni aceptación de epoch nuevo.

Baseline fresco una vez: 274 PASS = originales 266 + ocho nuevos; mismos 13 CPU deseleccionados. Tests previos: AST/asserts/decoradores/parámetros íntegros y fuentes protegidas byteexact. Lint y formato owned2 pasan. Cobertura WHOLE oficial líneas+ramas por fichero, única UUID `969e87e7-ee7a-4d2b-931b-44a182314c7f`: 300 RAW padre/hijos copiados antes de combine(keep=True). Sin unión de old266/276, exclusiones, extracción o media.

- `scripts\eval\benchmark_canonical_integration.py`: 86.940299 %, cero exclusiones.
- `scripts\eval\benchmark_canonical_runtime.py`: 85.441767 %, cero exclusiones.
- `scripts\eval\benchmark_coordinator.py`: 83.741648 %, cero exclusiones.
- `scripts\eval\benchmark_episode.py`: 87.078652 %, cero exclusiones.
- `scripts\eval\benchmark_process.py`: 81.777778 %, cero exclusiones.
- `scripts\eval\benchmark_runtime.py`: 80.516899 %, cero exclusiones.

Nativos: 301 nacimientos, disposiciones {'CLOSED_CONFIRMED': 257, 'UNKNOWN_QUARANTINED': 44}; 2 nacimientos sin traza persistida UNKNOWN. Fuente/test/runner/fixture/bootstrap copiados antes de Popen; argv/PID/UTC/Job FILETIME y referencias/waits contemporáneos en capturas cuando disponibles. Stderr nativo DEVNULL, RPC completo, instrucciones tras muerte y syscall de reader bloqueado permanecen UNKNOWN. Recetas previas copiadas antes de adaptar rutas privadas; fases cerradas conservadas. No freeze global de unidades disjuntas.

Formal4→5, componentinspection2→3 y T10 rebatido intactos. B4-02/03/04, CLI y transferencia ADR59 pendientes. Root realizará inspección fresca3 y QA independiente; esta entrega no acepta componente completo/T09/M0. Sin docs/ledger/Git/subagentes/goals/meter/GPU/UI/PDH/WSL/Docker/red/instalaciones. Contabilidad real de modelo/tokens/EUR/horas IA NULL. Historial de reparación privada: test movido tras imports antes de primera ejecución (no se llamó RED a un fallo de colección); formato owned2 antes del baseline.
