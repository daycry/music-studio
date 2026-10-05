# Revisión independiente de T-19 — intento 2

Fecha: 2026-10-06. Base `83fc652` más cambios sin comitear y nuevos. Traspaso completo desde [intento 1](review-1.md); se reevalúan las correcciones y se conservan los veredictos anteriores sin reabrirlos sin evidencia nueva. Tres revisores frescos A+B+C, independientes del implementador. A/B en paralelo; C después de terminar A por límite de threads. D no aplica. Scope exit 0, sin fuera de alcance, avisos ni exclusiones de usuario. Journals ajenos preservados.

## Veredictos por criterio

| Criterio T-19 | A: conformidad | B/C y evidencia |
|---|---|---|
| CA1: presupuesto nativo completo | ✓ conservado | `preflight.py:135/146/182`; métodos y límites del intento 1 sin cambios |
| CA2: rechazo previo y fallo cerrado | ✓ conservado | `server.py:182`, `adapter.py:477`; rechazo antes de cargar/registrar |
| CA3: caption largo y compatibilidad | ✓ conservado | `descriptor.py:64`, `test_preflight.py:221`; captions/seeds/shift/instrumental conservados |
| CA4: idioma y metadata sin reescritura | ✓ | `manifest.py:206/217/246`; efectivo/captura contrastados con solicitud; alias, metadata, omisión e instrumental probados |
| CA5: recibos efectivos verificables y privados | ✓ corregido | `manifest.py:217/232/246/261`; baseline original aceptado y tres contradicciones originales rechazadas; diez capturas integradas aceptadas sin alterar bytes |
| CA6: diferencial y límites artísticos | ✓ conservado | Corpus de 16 casos; evaluación de escucha §3.1 separa transporte, cumplimiento y naturalidad |
| CA7: TDD, cobertura y puertas | Parcial: QA pendiente | RED contractuales leídos, cobertura añadida 349/377 = 92,57 %, mínimo 86,05 %; revisión conforme, tarea todavía en revisión |
| Subtarea 5: puente T-08/T-12/T-13 | ✓ corregido | `tasks.md:346/358/440/462`; rúbrica y recibos enlazados, umbrales conservados |

A confirma alcance, constitución explícita y Verificación acreditada (146 passed, 1 skipped, exportador al día y cuatro manifiestos válidos). Interop y diff OpenAPI no aplican. No se utiliza la revisión para declarar QA ejecutada.

## Gaps y fusión

| ID previo | Grado | Tarea | Veredicto | Evidencia |
|---|---|---|---|---|
| A1 | Minor | T-19 | corregido | Evaluación de escucha §3.1 y notas de T-08/T-12/T-13 aplican rúbrica existente a recibos y nuevas comparaciones |
| B-01 | Important | T-19 | corregido | B reproduce baseline válido y `INPUT_RECEIPT_INVALID` en idioma/shift/CoT; publicación y verificación comprueban semántica independientemente del hash |

**Sin gaps pendientes:** 0 Critical / 0 Important / 0 Minor. Sin rebates ni deuda aceptada.

## Evidencia ejecutada

A ejecuta 26 regresiones de semántica/publicación: **26 passed, 29 deselected**, exit 0. Lee los 18 casos de mutación, cuatro válidos, cuatro de publicación/verify, RED y cobertura. Recorre el diff por ficheros y mantiene aprobaciones anteriores.

B ejecuta preparación, generate, audio-post, preflight, common, adapter y contrato: **264 passed, 1 skipped**, exit 0. Sus probes independientes aceptan los diez recibos nativos y cinco casos adicionales válidos (alias coincidentes, metadata N/A, duración fraccionaria, negative_prompt e instrumental unknown). Rechaza las tres contradicciones originales con hashes recalculados. No altera bytes originales. Padre sin torch/transformers; diff-check exit 0. Cobertura leída del fix 22/23 = 95,65 % y del manifiesto cambiado 64/69 = 92,75 %; no se presenta como medición QA independiente.

C ejecuta regresiones de recibos/publicación: **38 passed, 17 deselected in 0,46 s**, exit 0. Revisa `manifest.py:202–262/354`: JSON, comparaciones y hashes sin ejecución/red nueva; rechazo antes de publicar y error sanitizado. Conserva controles de preflight previamente aprobados. **Sin hallazgos** ni escenario explotable nuevo que justifique CWE.

Los revisores no modifican producto, ledger, Git, modelos ni originales. Los temporales de la fixture existente de `tests/conftest.py` prevalecen sobre `--basetemp` y usan también la caché de T-03; se declara y no se limpia contenido ajeno. Evidencias propias en la caché de T-19. Sin GPU, inferencia ni instalaciones.

Ventana conjunta 22:53:00–23:01:38 UTC, `fuente: estimado`; tokens, coste y horas IA reales desconocidos (`null`). El reloj de nueve minutos no es consumo IA. Marcador cerrado antes de QA; Jira/Confluence desactivados. QA independiente y cierre técnico de T-19 siguen pendientes; M0 y la calidad musical permanecen abiertos.
