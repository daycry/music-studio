# T-16 — revisión1 de propuesta diagnóstica: un Important

2026-10-06. A y B frescas, secuenciales por cupo de threads, independientes de autoría; alcance exclusivo de propuesta privada, no reinicia revisiones de productoSFT ni de arnés6tomas. [Diagnóstico previo](retry2-diagnosis-cpu-report.md). Fuentes originales bc798009 preservadas. C/D del selectorGit no disparan sobre caché ignorada; B comprueba propiedad/privacidad como corrección. No huboGPU ni cambios de producto.

| Criterio | A | B |
|---|---|---|
| Alcance privado e integridad29SHA | Conforme | Conforme |
| Una toma30s, parámetros/entradas originales | Conforme CPU, no reproduce90s | Conforme leído |
| Factoría ligera y módulo hijo importable | Conforme, IPC previo con dobles declarado | Conforme, wrappers normal/class/static CPU |
| Guardas, cap, monitor y cleanup propio | Conforme leído, antecedente sellado | Conforme leído, sinGPU |
| Propagación de fallo/parada/unload | No detectado enA | **B-01 Important** |
| Honestidad causal y CA3/4 abiertas | Conforme | Inferencia no verificable |
| E2/E3/OpenAPI | Conforme/n/a | Fuera de lente |

## Gap aceptado

B-01 Important: proposed-one-take.py121–129 registra exit_code/stop_reason/unload, pero no propaga fallo al proceso. ProbeCPU AST del try/finally exacto, sin FS/GPU/Torch: CLI1/null/unloadtrue→wrapper0; CLI1/paradapresupuesto/unloadtrue→wrapper0; CLI0/null/unloadfalse→wrapper0. A no detectó ese caso; no es rebate ni prueba de causa del fallo nativo. Root acepta el defecto.

A verificó29SHA/seisAST3.11 y prepare-onlyexit0; leyó IPC previo202/error/otroPID/padre sinTorch y límites CPU. B verificó29SHA y bindings/excepciones/progreso con dobles AST, seis tipos de traza. Fixture inicial sinSTDOUT corregida antes de evidencia; no error de producto. Ninguna inferencia real ni QA GPU acreditada.

## Fix1 separado para revisión2

Root conservó original bc798009 y creó candidato privado separado `.cache/dev-cycle/t16/diagnostic-fix1/run-one-take.py`, SHAe6fd237e2b035154822455a83e0b1adfbc82260570abf76c54da3f28257df82c. Único cambio tras try/finally: exit1 siCLI!=0, stop_reason noNone o unload no confirmado. Cleanup y captura se mantienen antes de propagar error.

RED real: `test_diagnostic_exit_reflects_generation_and_unload` falló en los tres escenarios con AssertionError DIAGNOSTIC_EXIT=0 required=1; caso conforme pasó. GREEN4passed0,06s, prepare-onlyexit0, sinGPU. Primeras fixtures KeyErrorstate/NameErrorendpoint conservadas y no contadas comoRED. Archivo candidato es copia sin cambios del baseline hasta RED. Test y fuentes congelados; no se reemplaza receipt29SHA anterior. La ejecuciónGPU espera revisión2 y QA del fix; T-08 puede validar su GPU por separado, sin modelos simultáneos.

Medidor fix1 02:17:25–02:19:55UTC,2m reloj/estimado/null; incluye cierreQA y comienzoGPU T08 concurrentes, no consumo IA individual. Revisión2 con tabla completa previa, sin reabrir conformidades salvo evidencia nueva. CA3/4/T16/M0 siguen abiertas.
