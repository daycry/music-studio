# T-08 — instrumentación diagnóstica ASR: A+B conformes, D pendiente

2026-10-06. Propuesta privada de dos archivos, sin fix de ASR ni causa probada. Baseline producto/imagen306e3b0; independiente de la corrección CLAP. Scope0sinavisos/exclusionesusuario; selectorCfalse/Dtrue por ruta cache. Lentes A+B frescas independientes de implementar; Dfresh rechazado por límite de threads y pendiente, no se presenta como pasado.

| Criterio | A | B |
|---|---|---|
| Factory importable en hijo y padre sinTorch | Conforme, import/preflight propios CPU | Conforme, cadena fresh éxitoPID7→11/errorPID16→20 |
| Algoritmo/loaders/cap/preflight originales | Conforme, delegación a imagen306e3b0 | Conforme, lectura completa/guardaslibre−512 |
| Inputconfined/SHA/n_outputs2/terminal yexit | Conforme, preflightrechaza2/error→2 | Conforme, éxitoexit0/error2 yterminalúnico |
| Trazasprivadas exclusivas fueraTMP/normal sincontenido | Conforme, UUID/x/mínimometadata | Conforme, delegaciónerrores ynormalcontenidoomitido |
| Unload/PID/PPID/borradoTMPfallido | Conforme evidenciaCPU | Conforme propiaCPU, descargado yTMPfallidoborrado |
| Alcance/estado/constitución/documentación | Conforme,2SHA/no producto niCA cerrado | No defectos nuevos, sinlectura conocimientoajeno |
| GPUreal/cancelación/QA yperformanceD | Pendientes | Pendientes |

A y B ceroCritical/Important/Minor, sinrebates/deuda. A ejecutó hash/importaciónfactory/preflightn_outputs2 en CPUoffline sinTorchpadre; un primer AST sobre BOM falló por decodificación del comando y se corrigió, sin producto. B ejecutó el runner real con dos cómputos dobles en destinos nuevos/tmpfs de imageninmutable, successdoneexit0/error2, otroPID/unload/TMPcleanup; driverREVIEW_B_CPU_RUNNER_OK=2exit0. Primer arnés B falló al crear/data antes de ejecutar runner, corregido con tmpfs. Ninguno cargó pesos niGPU ni tocó host/producto/Git/ledger/knowledge.

Falta D, fusiónfinal y QA antes de pruebaGPUdiagnóstica. Root deberá comprobar baseline≤1600/Ollamavacío/serialización y contenedor propio concleanup. Esto no valida cancelación real ni causa/precisión ASR. T08CA/M0 abiertos. Mediciónglobalenlote, sinconsumoindividual.
