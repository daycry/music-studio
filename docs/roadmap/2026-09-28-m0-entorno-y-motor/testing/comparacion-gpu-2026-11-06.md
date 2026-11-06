# Comparación observada SFT/Turbo — M0/T-16

Fecha: 2026-11-06. Seis salidas válidas; **ninguna de las tres parejas queda certificada**. Estado en el [ledger canónico](../tasks.md).

## Qué evidencia faltaba

Las seis tomas históricas conservan audio y recibos válidos, pero carecen de las observaciones necesarias para certificar identidad de códigos y backend. La [entrega CPU](condicionamiento-cpu-2026-11-06.md) añadió observaciones opcionales; esta ejecución genera tomas nuevas sin reescribir las anteriores.

## Cómo se preparan las seis tomas

La CLI existente ejecuta dos jobs independientes de tres variantes: uno Turbo y otro SFT. Cada lote utiliza semillas 1, 2 y 3 e índices 0, 1 y 2. El proceso permanece cargado entre variantes y se descarga entre lotes. No son seis arranques fríos ni un nuevo benchmark T-09.

| Entrada o control | Turbo | SFT |
|---|---|---|
| Duración solicitada | 90 s | 90 s |
| Checkpoint | `acestep-v15-turbo` | `acestep-v15-sft` |
| Pasos | 8 | 50 |
| CFG explícito CLI | Omitido | 7 |
| LM / backend / precisión | 0.6B / PT / BF16 | Iguales |
| Idioma / BPM / shift | es / 94 / 1 | Iguales |
| Semillas / variantes | 1, 2, 3 / tres | Iguales |
| Declaración de autoría | `own` | `own` |

Ambos lotes leen la misma letra y estilo privados de «Libre». SHA-256 de letra: `421a2aaa97998b38b71db4aa939f468e4f6fb54a0b3d0c895d93fbae7ad5e635`; estilo efectivo: `22471b4c4326638c937d5ac12347ca84ddc3b90407a590f3d5abcdc071e1757b`. El estilo procede del archivo original, retirando sólo el espacio final ya declarado en la preparación.

La imagen ya verificada en [T-09](benchmark-basico-2026-11-06.md) es `sha256:761384424101a4b7c24994d124bed352594c230f6a50bec59327a3ef6916de56`. La configuración del checkpoint cambia entre contenedores aislados; no cambia el código del producto. `STUDIO_ALLOW_UNVERIFIED=1` habilita la comparación sin cambiar la aceptación del descriptor.

## Qué se exige para certificar cada pareja

El validador existente recibe la solicitud esperada construida desde los inputs y controles independientes. Usa `private_params=True`, `require_conditioning=True` y el índice real 0, 1 o 2 de cada variante.

Después se comparan letra, caption, idioma, duración, BPM, shift, semilla, controles LM y las observaciones de cada ejecución. Las diferencias esperadas son checkpoint, pasos y la opción CFG de la solicitud. Los hashes completos de argumentos contienen esos controles; no sirven como condición de igualdad.

Ambos recibos deben acreditar backend observado `pt`, LM ejecutado y `thinking:true`. En `dit_resolution` se exige `initial_task:text2music`, `has_audio_codes:true`, `resolved_task:cover`, instrucción válida y huellas de códigos iguales por semilla. El resolver nativo usa `cover` al recibir los códigos LM, según [ADR-0032](../../../decisiones/ADR-0032-condicionamiento-dit-segun-rama-nativa.md).

La igualdad de dos huellas de `None` o de otros valores vacíos no acredita códigos LM efectivos. El booleano observado `has_audio_codes:true` excluye esos casos. Este contraste acredita el argumento de códigos no vacío en la frontera del resolver; no acredita identidad de los latentes posteriores ni calidad musical.

## Resultados y cierre

Los dos jobs terminaron con CLI exit 0 y `spilled:false` literal. Los seis manifests, recibos fuertes y audios pasaron la validación: 90 segundos, 48 kHz y estéreo. El primer lote alcanzó 9.446 MiB de pico host y el segundo 9.444 MiB. La telemetría agregada de cada lote no equivale a tres mediciones independientes.

| Semilla | Backend observado en ambos | Códigos no vacíos | Huella Turbo (prefijo) | Huella SFT (prefijo) | Pareja |
|---|---|---|---|---|---|
| 1 | PT | Sí | `95ccc4081e98` | `10d5dcc77872` | No certificada |
| 2 | PT | Sí | `2dd7d2e2410` | `ebb94d229e26` | No certificada |
| 3 | PT | Sí | `8eebb07e8dc9` | `e43a0d42303a` | No certificada |

Por pareja coinciden los prompts y argumentos LM capturados, los tokens DiT y la resolución salvo la huella de códigos. También coinciden solicitud y parámetros efectivos salvo los controles DiT previstos. **Las huellas de los códigos difieren en las tres parejas.** La entrada textual llega igual al LM; esta evidencia no permite atribuir la diferencia musical sólo al checkpoint DiT.

El [resumen QA](../../../../.cache/dev-cycle/20261106-m0-t16/gpu-pairs/qa/summary.json) conserva `status:not_certified`, las seis filas y todos los checks por pareja. El [informe de ejecución](../../../../.cache/dev-cycle/20261106-m0-t16/gpu-pairs/qa/report.md) mantiene el resultado negativo. No se modificaron los históricos ni se repitieron generaciones para cambiar ese resultado.

Los tiempos de pared del observador incluyen replay y descarga: `observer_launch_to_unload_s`. El campo original `cli_wall_s` del harness estaba mal nombrado y se conserva en el raw. Sólo `telemetry.extra.inference_timings` representa la inferencia sincronizada.

QA retiró los contenedores propios y conservó la demo. Los 33 archivos de modelos seleccionados, 68 fuentes y 71 archivos ajenos mantienen sus hashes. Ollama siguió vacío; GPU final 1.227 MiB. La [hoja de escucha exploratoria](../../../../.cache/dev-cycle/20261106-m0-t16/gpu-pairs/qa/listening/listen.html) conserva el aviso de comparación no controlada y permite exportar valoraciones; no hay ganador declarado.

## Qué demuestra el diagnóstico de la semilla

`custom-agents:debug-root-cause` aisló la ruta PT de la fuente exacta exportada de la imagen. En `generate_with_stop_condition`, la rama individual no propaga las semillas a `generate_from_formatted_prompt`. La rama individual de `_run_pt` no reinicia el RNG; `_sample_tokens` usa `torch.multinomial` global sin generador explícito.

La [prueba CPU AST/mock](../../../../.cache/dev-cycle/20261106-m0-t16/gpu-pairs/diagnosis-seeding/probe-result.json) ejecutó funciones extraídas de esa fuente. Con la misma semilla, cambiar el estado previo modifica el resultado individual; cambiar sólo la semilla no lo modifica. La rama de lista sí reinicia el RNG. Los hashes de las fuentes coinciden con el perfil vigente y la imagen ejecutada.

Esto demuestra que la semilla no controla el muestreo PT individual por esa ruta. No demuestra qué operación concreta creó la diferencia de estado GPU ni que un reinicio baste para igualar las tomas reales.

## Corrección CPU preparada para revisión

El contexto propio `lm_seed` envuelve temporalmente `_run_pt_single`. Aplica la semilla efectiva de cada variante mediante `runtime.torch.manual_seed` y restaura el método en `finally`. El cambio queda separado de la captura; mantiene argumentos LM, prompts, controles DiT y fuente upstream fijada.

Los tests de integración con RNG falso fallaron antes del código: una misma semilla dependía del estado previo y la variante de semilla 0 producía otros códigos. Tras el cambio pasan ocho casos. Incluyen semillas efectivas, variantes, errores, cancelación y restauración del método. No importan Torch real.

El implementador obtuvo 180 aprobadas y una omitida en la regresión focal; la verificación canónica exacta dio 41 aprobadas, cero omitidas. Ruff pasó para los dos archivos. La cobertura oficial del delta es 15/15 sentencias, 100 %; la del archivo completo es 67,77 %. El cálculo incluye el nodo `with` que ejecuta el nuevo contexto multilínea.

La primera invocación de cobertura no produjo datos por usar una ruta de archivo como módulo; el cálculo válido procede de una corrida corregida con `--cov=adapter`. No se mezcla con esa corrida sin cobertura. [Evidencia TDD y comandos](../../../../.cache/dev-cycle/20261106-m0-t16/gpu-pairs/seed-fix/evidence.md).

Revisión A/B del fix, intento 1: sin hallazgos; ocho archivos en alcance, sin exclusiones ni avisos. El selector no activó C ni D. Ambas lentes contrastaron el control de semilla y la restauración; B ejecutó las ocho regresiones. [Veredictos](../../../../.cache/dev-cycle/20261106-m0-t16/gpu-pairs/review-1/verdicts.md).

QA CPU independiente: **478 aprobadas, 10 omitidas, cero fallos**, 488 casos, 30,75 segundos. Incluye los 41 canónicos y las ocho regresiones nuevas; sin importar ni intentar importar Torch. Cobertura de esta selección: delta 15/15 sentencias, 100 %; archivo completo 322/394, 81,73 %. No se combina con el 67,77 % de la selección focal del implementador.

Ruff, diff-check y ledger-lint pasaron; el ledger conserva 25 avisos históricos. QA confirmó ocho pins, 67 fuentes sin cambios y la modificación autorizada del adapter; 71 archivos ajenos intactos. Cuatro enlaces rotos de `pipeline-audio.md` ya existían en la base; ninguno nuevo está roto. Un `PytestCacheWarning` de renombrado Windows no afectó al batch y no motivó repetirlo. [Informe QA CPU](../../../../.cache/dev-cycle/20261106-m0-t16/gpu-pairs/seed-fix/qa/report.md).

El orquestador acepta la entrega CPU. Los seis audios anteriores mantienen su resultado 0/3; la igualdad CUDA posterior requiere nuevas tomas. T-16, M0 y M1 siguen abiertos.
