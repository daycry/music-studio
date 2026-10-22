> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Diagnóstico acotado: entrega durante drenaje

PARTIAL. No se modificó producción y los dos módulos de tests quedaron restaurados a sus bytes originales. La regresión intentada se conserva sólo en `attempted-regression/` y en las copias anteriores al arranque del contenedor.

## Fase 1 — reproducción mínima

Se ejecutó una única regresión nativa Linux nueva: `test_real_wire_held_until_draining_retains_owner[truncated]`. Comando interno real, PID, UTC, stdout, stderr, JUnit y espera directa están en `runs/red-h1-linux/`. Resultado: 1 FAIL, sin errores de importación/colección. El fallo fue `assert 'cancelled' == 'transport_error'`; **no es el RED causal requerido**: la aserción UNKNOWN ya pasó. No se repitió el caso ni la suite original y no se ejecutó 801.

## Fase 2 — aislamiento

La fixture original creó líder/nieto reales y recibió el request por el writer nativo. El wrapper llamó al reader real, retuvo exactamente `000000107b`, sin fabricar bytes, y entregó esos mismos bytes sólo cuando el owner estaba DRAINING con stop activado. Orden monotónico observado: ready físico → request nativo retornado → lectura física retenida → cancel_requested → drain_delivery → EOF físico → join. La prueba anterior a las aserciones está en `proof/drain-truncated.json`.

El journal final registró leader_exit, líder status0, nieto status9, TERM/KILL reales, echild y confirmed=true. Sin embargo, la primera terminación no dio autoridad suficiente para cerrar; el owner acabó UNKNOWN_QUARANTINED/cancelled, con group.closed=false. La contención posterior registró waits nativos y mantuvo referencias. El journal final y la disposición final no sustituyen el valor original de retorno de terminate, que no se instrumentó. No se atribuye un motivo exacto no observado a ese retorno.

## Fase 3 — H1 y límites

H1: al entregar bytes malformados durante DRAINING, `_read(parsing=False)` consume la salida sin `decoder.feed`; `finish` ve un buffer vacío y stop suprime el EOF prematuro. La fuente muestra esta omisión y la prueba acredita la entrega controlada, pero el backend impidió el CLOSED que exige la demostración del defecto de aceptación. **Causa exacta del CLOSED de QA1 no probada**. H2 no ejecutada; no hay una segunda hipótesis declarada como probada. No se clasifica este fallo de motivo como un RED causal ni como GREEN de transporte.

## Fase 4 — no autorizada por evidencia

Se retuvieron todas las evidencias y se restauraron únicamente nuestras adiciones a los tests; custody.py nunca cambió. No se aplicó un parche a ciegas. No hubo baseline dualOS, cobertura aceptada, revisión nueva ni QA2: son posteriores a un RED causal y un fix. La siguiente prueba necesita controlar la entrega conservando autoridad real de terminación antes de evaluar CLOSED, con testigo ajeno y captura previa completa, sin falsear backend/kernel ni repetir hasta obtener el resultado deseado.

QA1 permanece 67 PASS/1 FAIL. Revisiones Linux1/2/3 y QA fallida conservan su historia sin reset. El fallo global de formato de contracts.py protegido sigue abierto; no se ejecutó ni se afirmó un nuevo gate de formato. No cambia la aceptación de T05, CPU2, audio, SQL, FS, FFmpeg, E2E, GPU o M0. No se tocaron ledger/docs/Git/meters/goals/knowledge ni unidades disjuntas. Modelo/tokens/EUR/horas IA: NULL.

La falta de captura completa del intérprete/dependencias antes de los imports del preparador se declara en receipt.json. El contenedor sí tuvo fuentes y herramientas copiadas con hash antes de start. No hay afirmación de supervivencia ajena sin testigo ni reconstrucción retroactiva de PID/UTC/FDs ausentes. Contenedor propio registrado antes de start, inspeccionado, eliminado y comprobado ausente con sus originales. Inventario privado incluye todo salvo los cuatro nombres reservados exactos del padre y el propio inventario.
