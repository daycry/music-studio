# T16: corrección privada del contrato del packer nativo

Estado: READY_FOR_REVIEW. Revisión adversarial y QA frescas pendientes; CA3, CA4, calidad musical y M0 siguen abiertos.

## Reproducción y aislamiento

El test ejecuta el bloque AST completo desde la guarda de seis rutas hasta el final de las guardas de igualdad LM/DIT/lm_metadata. Usa los seis manifests y recibos v2 auténticos sin modificarlos, comprueba SHA del payload y llama al validador actual de producto. Solo verify_manifest, SoundFile y measure_audio se aíslan con dobles: no se lee audio ni se ejecuta ffmpeg, normalización, copia, publicación o pack completo.

RED: test_contract.py::test_six_real_v2_receipts_complete_validation_contract falló con KeyError 'request' en línea 89 del bloque original. 1 failed, exit 1. Comando y timestamp exactos: red-run.json; salida: red.stdout.txt; JUnit: red.xml.

## Hipótesis probada

El packer interpreta erróneamente el sobre que devuelve validate_input_receipt. Los seis recibos válidos devuelven planned/captured y guardan request en planned.request. Los pasos y CFG están en planned.effective; no se trasladan. La primera corrección parcial reveló otro acceso incompatible: checkpoint vive en planned.checkpoint.id, no en planned.effective.checkpoint. Se confirmó esta segunda hipótesis en 6/6 recibos antes de modificar ese acceso. Inventario de rutas de claves/tipos, controles no sensibles y hashes de los seis planes: hypothesis-proof.json.

El intento intermedio se conserva íntegro (intermediate-request-fix*: 7 failed, 2 passed, KeyError checkpoint). Fue una hipótesis inicial incompleta, no otra generación ni otro ciclo QA. La petición posterior de auditar todos los accesos llegó después de la edición final; se completó el cotejo con el inventario estructural y el bloque íntegro en verde. La prueba principal sigue siendo la misma.

## Cambio mínimo y evidencia GREEN

Tres accesos, sin cambiar el validador ni relajar hashes, controles, idioma, caption o igualdad de pares:
- native.request.model_id → native.planned.request.model_id.
- native.planned.effective.checkpoint → native.planned.checkpoint.id.
- native.request.params.style → native.planned.request.params.style.

Delta exacto: delta.patch. El candidato completo es una copia derivada pack-comparison.py. AST compatible con Python 3.11; ejecución con Python gestionado 3.12.14.

GREEN: 9 passed in 0.20s, exit 0. Test principal: seis recibos v2, seis invocaciones del validador real y seis entradas producidas por el bloque. Ocho vecinos alteran en memoria, después de validar el recibo real, model_id, checkpoint, pasos, CFG, caption, LM, DIT o lm_metadata; cada conflicto sigue siendo rechazado por una guarda del packer. Comando y timestamp: green-run.json; salida: green.stdout.txt; JUnit: green.xml. No prueban autenticidad del objeto mutado, sino que las guardas propias del packer permanecen activas. No se ejecutan suites de producto ni GPU.

## Integridad y límites

Freeze before/after idénticos, rutas relativas a la raíz: 87 entradas; nueve fuentes de producto coinciden con el baseline publicado. Incluyen packers previos, configuración/plan nativo, fuentes de supervisión, evidencias previas y SHA de los seis manifests y seis recibos; no contienen audio, letra, estilo ni token. Los hashes del plan y supervisión también figuran en receipt.json. Los resultados de duración/loudness del doble no acreditan el audio real.

Las 20 pruebas de QA previas cubrían fragmentos/configuración estática y no la interacción completa con el envelope real: este fallo no invalida su prueba SHA/configuración, pero ese alcance no acreditaba el pack real. No se regeneran las seis tomas ni se reescribe ninguna evidencia anterior.

Incidentes del harness: el primer lanzamiento de run-tests.py tuvo TypeError por concatenación de Path antes de ejecutar pytest; no cuenta como RED. Se corrigió el runner y el RED válido fue KeyError request. RED emitió un aviso no bloqueante al crear caché pytest local; GREEN no lo emitió. Para crear la carpeta se escribió y eliminó inmediatamente un temporal fuera del ownership (.cache/dev-cycle/t16/create-fix-dir-temporary.py); su ausencia quedó comprobada, sin repetir escrituras externas.

Se omite memoria/gotcha/ADR por ownership expresamente prohibido; diagnóstico queda en este reporte privado y lo trasladará el orquestador al ledger. No se toca Git, docs, ledger, datos, pesos, Docker, jobs ni MCP.
