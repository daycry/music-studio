> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

QA independiente sobre código actual y copias físicas. OWNERSHIP []. Root conserva aceptación y ledger.

UUID: d2577bc5-404e-47d3-84c9-5b718b16014d. Linux {'cases': 32, 'failures': 1, 'errors': 0, 'skips': 0}; Windows {'cases': 36, 'failures': 0, 'errors': 0, 'skips': 0}.

Cobertura WHOLE oficial líneas + ramas, sin exclusiones ni unión histórica:
- apps/server/app/worker/custody.py: 258/293 = 88.05460750853243 %.
- apps/server/app/worker/custody_linux.py: 285/333 = 85.58558558558559 %.
- apps/server/app/worker/custody_linux_supervisor.py: 262/327 = 80.1223241590214 %.

Gates: {"source_same": true, "physical_input_same": true, "raw_copy_same": true, "case_parity": true, "linux": false, "windows": true, "whole_each80_zeroexclusions": true, "official_and_lint_exits0": false, "container_removed": true}

RAW actuales padre/hijos de ambas OS copiados ANTES de combine --keep: 67. Pathmaps y fuentes en official-current/raw-traces-before-combine.json. Originales/asserts/decoradores/parámetros conservados byte/AST; seis casos añadidos actuales incluidos. Ruff check/format --check sobre alcance real, salidas/exits originales guardados.

Un único contenedor propio exacto 0ea7e9f2a5fc47a209bba733c1b6f0e363d1588d75417008fb9808c57437686b; create/registro antes de start, inspect/remove/gone guardados. Imagen existente fijada, sin build/pull/instalación/red/GPU; límites solicitados en container-custody.json.

B01 EMFILE mantiene grupo UNKNOWN y referencias parciales; B02 ENOSPC/EIO cierra árbol propio sin elevar scope; B03 registra TERM real antes del fallo controlado y KILL/waits antes del rescate con testigo ajeno vivo. Notify ValueError no da evento final al consumidor aunque journal previo confirmado; PGID EIO no autoriza señales de grupo, fallback sólo pidfds propios y confirmed=false. Observaciones actuales en fault-observations.json y nativecaseoutcomes.json. Fallos inyectados controlados no prueban fallo espontáneo del sistema.

Birth/kernel PID/FILETIME/Job/PGID, pidfds, waits/EOF/readers/writers/refs sólo según assertions y artefactos efectivamente capturados. UTC tras Popen es post-observada; campos individuales ausentes UNKNOWN. resource_returned permanece UNKNOWN donde falta prueba de FD/hilos/refs, no inferido de Job vacío ni éxito del test. Fixtures fijas confiables; no garantía universal frente a escape malicioso.

Historia bootstrap1: Linux falló antes de crear contenedor por runs ausente; Windows 27FAIL/9PASS por intérprete gestionado externo a la raíz física copiada. Se guardó todo; reparación exclusivamente privada copiando intérprete existente y carpeta runs, sin cambiar producto/tests/plazos. Nuevo UUID y baseline dual actual única; no RED causal ni QA verde del intento previo.

current_sources.json es observacional, no propiedad. Alcance protegido propio antes/después; cambios M0/cola disjuntos no congelados. TDD n/a QA-only. No docs/Git/ledger/knowledge/meters/goal editados. Modelo/tokens/EUR/horas IA NULL. No aceptación completa T05, GPU/E2E/audio/FFmpeg/FS/CPU2/SQLite/calidad musical; root adjudica componente.

Resultado final: 67PASS/1FAIL/0ERROR/0SKIP. FALLA test_invalid_transport_retains_owner[truncated]: esperaba UNKNOWN_QUARANTINED, recibió CLOSED_CONFIRMED. Journal reason=stop, líder status0/nieto status9, cierre FD registrado. La ordenación temporal de bytes/deadline no fue capturada: causa exacta UNKNOWN; hipótesis estática y evidencias en root-diagnosis.json. No rerun funcional ni fix. Ruff check exit0; format --check exit1 sólo en contracts.py protegido e intacto. Paquete FALLIDO para diagnóstico de root, sin aceptación.
