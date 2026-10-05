# Revisión independiente de T-19 — intento 1

Fecha: 2026-10-06. Base `83fc652` más cambios sin comitear y ficheros nuevos. Lentes A+B+C, cada una con contexto fresco, sin ver implementar. Leído el diff completo por bloques: 31 ficheros de la tarea; journals ajenos excluidos por instrucción. Scope exit 0, sin avisos ni exclusiones de usuario. Selector C por `exec` en preflight; D no aplica. La limitación de threads impidió lanzar C junto con A/B; se lanzó después de terminar A, en un contexto nuevo. No se sustituyó esa lente por una revisión del implementador.

## Veredictos por criterio

| Criterio T-19 | A: conformidad | B: corrección | Evidencia |
|---|---|---|---|
| CA1: presupuesto completo y métodos nativos | ✓ | ✓ | `preflight.py:35/135/165/182`, tests de límites exactos/+1; recibo integrado de 16 casos |
| CA2: rechazo previo a carga/cola y fallo cerrado | ✓ | ✓ | `server.py:182`, `adapter.py:477`, `preflight.py:331`; HTTP/directadapter y cero load/job ante rechazo |
| CA3: caption largo compatible, seeds/shift/instrumental | ✓ | ✓ | `descriptor.py:64`, `test_preflight.py:221`, HTTP caption 600; asserts anteriores preservados |
| CA4: idioma YAML/DiT y metadata sin reescritura | ✓ en generación | ✓ en generación | `adapter.py:294/333`, `preflight.py:143/168`; pruebas de metadata y captura |
| CA5: planned/captured verificables y privados | ✓ según lectura A; fusión ✗ | ✗ | La reproducción B prueba que la publicación admite contradicciones entre solicitud y efectivo; no queda acreditado para cierre |
| CA6: diferencial de 16 casos, límites artísticos explícitos | ✓ | ✓ | PT real antes del forward sustituido, hashes de ambas ramas y reserva; tags no equivalen a obediencia musical |
| CA7: TDD, cobertura, restricciones y puertas | Parcial; cierre pendiente | Parcial; cierre pendiente | 327/354 = 92,37 %, mínimo 86,05 %; padre fresco sin torch/transformers; QA aún no ejecutada |

Subtareas 1–4 acreditadas por lectura A de RED/GREEN; el hallazgo B obliga reforzar la cuarta. Subtarea 5 parcial: contratos, ADR y arquitectura conformes; falta puente documental explícito hacia la rúbrica existente. Constitución, alcance, evidencias declaradas y generados: conformes en A. Interop/OpenAPI no aplican al diff.

## Gaps completos para el siguiente intento

| ID | Grado | Tarea | Fichero:línea original | Escenario | Veredicto |
|---|---|---|---|---|---|
| A1 | Minor | T-19 | `tasks.md:674` | La subtarea exige incorporar dependencias/rúbrica de T-08/T-12/T-13. La rúbrica ya existe en `testing/t18/preparation-report.md:23`, pero esas tareas no enlazan su aplicación ni los recibos. Las puertas artísticas vigentes permanecen, por eso Minor | pendiente |
| B-01 | Important | T-19 | `packages/audio-post/audio_post/manifest.py:207/267` | Petición language=es/shift=3 con efectivo/captura en o shift=1, o los tres flags CoT true: al recalcular hashes, generate → publish_input_receipts → write_manifest → verify_manifest publica un manifiesto válido contradictorio | pendiente; confirmado por root |

No hay Critical ni hallazgos de seguridad introducidos. La lente C no convierte el hallazgo de integridad B en una vulnerabilidad sin escenario explotable. La graduación de B obliga corrección; no se acepta como deuda ni se rebaja para cerrar.

## Evidencia ejecutada por los revisores

A reprodujo la Verificación declarada: **120 passed, 1 skipped**, exit 0. Exportador **engine-v1.json up to date**, cuatro ejemplos **all valid (4 manifests)**, importación fresca `torch_parent=False/transformers_parent=False`, diff-check exit 0. Leyó todos los recibos nativos, probe, RED y documentación. Un aviso de cache_dir ocurrió al desactivar cacheprovider; no se oculta ni se trata como fallo.

B ejecutó los cinco módulos declarados: **120 passed, 1 skipped**, exit 0. Reprodujo baseline y tres mutaciones con descriptor/schema reales, transporte/audio sintéticos y publicación/verificador reales. Los cuatro resultados eran `valid: true, outputs: 1`. Root leyó esos recibos nuevos y reprodujo la aceptación de las tres contradicciones con `validate_input_receipt`, sin tocar originales. Evidencia privada en `.cache/dev-cycle/t19/review-b/`; no se publica texto de usuario. Un intento inicial de fixture carecía de tools.lock y falló FFMPEG_REQUIRED; la reproducción final usó la raíz real del proyecto.

C ejecutó preflight/common/preparation: **72 passed in 3,96 s**, exit 0. Las probes en memoria comprobaron hash de fuente alterado → WEIGHTS_MISMATCH antes de runpy y estimate/jobs sin token →401/cero invocaciones preflight. Lectura de todo el diff: argv fijo/JSON por stdin, código fijado antes de exec, tokenizadores offline, safe_path, CAS atómico y errores privados; **sin hallazgos**. No se ejecutó una auditoría completa del proyecto.

Sin GPU, inferencia, instalaciones ni cambios de producto de los revisores. Marcador conjunto cerrado antes del fix; medición estimada, sin tokens/coste/horas IA reales. Jira/Confluence desactivados. Root conserva ledger, corrección e integración; QA independiente sigue pendiente.
