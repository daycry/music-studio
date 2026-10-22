# ADR-0039 — Readquisición WDDM acotada

- **Estado:** aceptada; implementación, QA y acreditación GPU pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo la delegación autónoma del propietario
- **Ámbito:** M0/T-09; complementa ADR-0036 mediante una política nueva, sin recalificar el histórico

La matriz anterior se detuvo con18done y1cancelled. Un original contiene NVML9304MiB y PDH9009,68MiB, fuera del contraste permitido. El siguiente original,133,42ms después, contiene8996/9009,68 y pasa el mismo validador. El replay conserva el rechazo anterior y descarta errores de timestamp, escala e identidad en esas muestras. La adquisición secuencial puede atravesar una transición; el mecanismo interno del driver no está demostrado.

Un arquitecto fresco comparó parada inmediata con resumes repetidos, readquisición completa acotada y un bracketNVML–PDH–NVML. Se elige la segunda opción: permite recuperar una transición únicamente con otro original válido, añade menos consultas y no amplía el margen de contraste.

La política nueva fija **un solo reintento completo**, sin espera añadida, con presupuesto total de **2 segundos desde el inicio de la primera adquisición**. Se comprueban todos los controles salvo el contraste dedicado antes de clasificar una discrepancia como recuperable. Cualquier otro fallo detiene inmediatamente. Ambas adquisiciones se conservan como originales ordenados, con contexto, relojes, resultado y enlaces verificables. El validador recalcula el episodio; no acepta originales omitidos, sustituidos o fuera del presupuesto.

Solo se acepta la segunda adquisición si satisface todos los controles, el presupuesto y la cadencia respecto al predecesor. Una segunda discrepancia detiene el lote. Se mantienen128MiB/2%, consulta≤2s, skew≤1s, tick≤2,5s, frescura900s, identidad, rawcounts y navegador. Un reintento no relanza inferencia. Las diez muestras aceptadas de cada fase de calibración siguen siendo necesarias y los rechazos se conservan por separado. Una discrepancia intermedia rompe la consecutividad para afirmar elevación sostenida de shared.

El cambio exige versión de política, fuentes selladas, plan y sesión nuevos de160ejecuciones. La sesión anterior y sus18tomas se publican separadamente; no se editan sus hashes ni se combinan como si procedieran de una sola sesión con fuentes fijas. `provider_verified` sigue sin equivaler a validación independiente ni a ausencia causal de spill.

[Diseño y verificación previstos](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/bounded-reacquisition-design.md). TDD, revisión A/B/D y QA independientes antes de otra GPU. La descarga propia y la recuperación de VRAM de la sesión fallida están acreditadas; el benchmark completo y la calidad musical permanecen pendientes.
