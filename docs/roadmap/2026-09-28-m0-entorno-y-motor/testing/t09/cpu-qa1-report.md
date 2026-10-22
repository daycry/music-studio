# QA independiente T-09 CPU — intento 1

Estado: **CPU_QA_FAIL por formato**. La suite funcional pasa: **272 passed, 5 skipped, 1 GPU deselected, 1 warning**,23,13s. JUnit confirma277casos,272passed/5skip/0fallos/0errores. Cobertura oficial15módulos: media87,551085574%, umbral80; mínimoindividual67,961165% informativo. Las33fuentes coinciden con fix3 antes/después de la auditoría. Root cotejó artefactos y JUnit. [Recibo](cpu-qa1-receipt.json).

Ruffcheck32Pythonexit0, formatcheckexit1. El lockJSON restante es válido e íntegro. Tres tests requieren formato: test_adapter.py431, test_review_fixes.py95, test_shift.py113/120. La comparación contra la copia pre-T09 prueba que esos lugares cambiaron en la entrega originalT09; baselineformato0, actuales idénticos porSHA desde cpu-delivery hasta fix3. No son deuda anterior ni regresión de los fixes1/2/3. No se modifica el veredicto para ocultarlos.

Ledgerlint0/6avisosChangelog futuros; coverage-check0. ℹ️ sinUI por diseño (`test-plan: n/a (sin UI)`), coberturaE2E exenta, eximidosT00–T19/eximidos_exigidosfalse, rutasUI[]/origen{}/degradadonull/marcador_no_canóniconull. No se ha ejecutado coberturaE2E ni qa-gatePlaywright; n/a por exención explícita, sin resultados inventados. El recibo conserva el JSON íntegro de la declaración.

Root coordina una corrección automática de formato en esos tres tests, con igualdadAST antes/después, preimágenes y nuevo freeze. Después, revisión del delta y QA intento2. No se reabre R09-08 funcional ni se repite la suite antes de modificar/verificar esa corrección. No hay QAverde aún.

GPU, imagen/runtime, matriz160jobs, calibraciónTaskManager/navegador, RTF, spill, XL/offload y calidad siguen pendientes; T09/M0 abiertos. ComputerUse sigue detenido porEscape. Auditoría sinGPU/Docker/red/modelos/audio/UI/instalación/knowledge/memorias. TDDn/a: informe; QA no se atribuye RED funcional.
