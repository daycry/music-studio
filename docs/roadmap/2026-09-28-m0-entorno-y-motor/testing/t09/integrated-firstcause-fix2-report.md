> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# FC01 — unidad concreta para revisión

Cambio limitado a los dos ficheros autorizados. El registro canónico de cleanup usa `safe_cleanup_error_record`, inicializa evidencia secundaria tipada con digest/reloj UNKNOWN y protege también el propio logger seguro. La excepción WorkerFailure primaria se relanza con `raise` para conservar su traceback. Sin error primario, el comportamiento de close sigue propagando el fallo.

RED causal genuino previo al producto: `red-record` y `red-record-evidence` fallaron con identidad OSError en lugar de PrimaryFailure. La repetición guardó llamadas y estados antes de rescue: ingesta real, terminación del Job canónico, registro fallido, sensor aún vivo; sin interrupción registrada. Fallos CONTROLADOS, no avería espontánea/kernel. Los tres parámetros GREEN incluyen logger normal, logger fallido y logger seguro fallido. Sesión/Acquirer/Jobs/readers reales; witness extranjero vivo e identidad intacta antes de rescue. Se restauran faults antes de cerrar exclusivamente referencias propias.

La interrupción inmediata es memoria (dict/list), no escritura de fichero; no se afirma persistencia durable ni se fabrica un RED de I/O. Las regresiones verifican identidad/tipo y nodo original del traceback, intento de cierre sensor, interrupción en memoria, ausencia de recibo/head positivo, evidencia UNKNOWN y supervivencia extranjera.

Baseline fresco UNA vez: 266 PASS, 13 deselect originales (263 previos + 3 nuevos). Las siete suites originales completas se recopilan con la selección CPU original. Funciones/decoradores/parámetros/asserts previos de integración idénticos por AST; fuentes/tests protegidos idénticos por bytes.

Cobertura oficial combinada línea+ramas WHOLE6, única UUID `2698d906-44f5-4722-8246-06c20dd0e1c7`. 276 RAW frescos padre/hijos, copiados antes de combine(keep=True); no reutilización de final03, extracción, medias, unión histórica ni exclusiones.

- `scripts\eval\benchmark_canonical_integration.py`: 86.940299 %; 0 exclusiones.
- `scripts\eval\benchmark_canonical_runtime.py`: 84.279919 %; 0 exclusiones.
- `scripts\eval\benchmark_coordinator.py`: 83.741648 %; 0 exclusiones.
- `scripts\eval\benchmark_episode.py`: 87.078652 %; 0 exclusiones.
- `scripts\eval\benchmark_process.py`: 81.777778 %; 0 exclusiones.
- `scripts\eval\benchmark_runtime.py`: 80.516899 %; 0 exclusiones.

Nativos: 277 births; disposiciones {'CLOSED_CONFIRMED': 241, 'UNKNOWN_QUARANTINED': 36}. UNKNOWN conservados; salida de proceso no libera por sí sola resource gate. Stderr DEVNULL y transcripción RPC completa UNKNOWN. Recetas previas bytecopiadas antes de uso, templates sin modificación. Fuente/test/runner/fixtures archivados antes de Popen; refs/argv/PID/UTC y cleanup son contemporáneos cuando hay evidencia. Capturas iniciales incompletas permanecen UNKNOWN.

Historial: primer GREEN seguido de cambio real (fallback tipado/assert de logger), segundo GREEN; lint de formato detectó línea nueva larga y se corrigió sólo formato antes del baseline. No cambios de plazos/CONTEXT/selección/exclusiones. Los datos de tokens/modelo/EUR/horas IA son NULL.

No aceptación de componente/T09/M0/CLI/FINAL/GPU. Pendientes inspección fresca 2 e independent QA por root. B4-02/B4-03/B4-04/ADR59 y R09T13 no implementados. Sin docs/ledger/Git/subagentes/host Python/GPU/red.
