# T-16 — revisión de dos lentes, intento 1, tramo CPU

Fecha: 2026-10-06. Base `ef66a36bedf08fb996f88ef6cb9633b5f51f13b8` más cambios locales/nuevos. Lentes A+B frescas e independientes de implementación. B se lanzó después de A por límite de threads; no se reutilizó contexto. El selector determinista dio C=false/D=false, sin motivos ni avisos. Scope exit 0: ningún archivo fuera de alcance ni exclusión de usuario. Journals ajenos excluidos por regla predeterminada, sin lectura ni promoción.

## Lente A

[Tabla completa conservada](review-1-a.md): identidad, defaults/límites, CLI/manifiestos, progreso, planned/captured, constitución, alcance, cobertura y documentación conformes. 104 pruebas propias y una del hook real verdes; cruce de cobertura oficial 59/63=93,65 %, mínimo del diff 86,36 %. Sin gaps. CA2 aún requiere QA y CA3/4 siguen pendientes de ejecución GPU/escucha.

## Lente B

Revisor fresco `/root/review_t16_1_b`, perfil backend. Leyó el diff por archivos y validó las capturas privadas sin cambiar sus bytes.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Identidad y controles Turbo/SFT | ✓ | descriptor.py:19, adapter.py:306, input_profile.py:6; identidad/defaults/inválidos |
| CLI, briefs y solicitud explícita | ✓ | generate.py:153,386; overrides, preparación, publicación y rechazo antes de HTTP |
| GenerationParams/progreso/cancelación | ✓ | adapter.py:535; reproducción SFT legado sin model_id →50/7, cincuenta callbacks Euler y cancelación con retirada de hooks |
| Planned/captured y legado | ✓ | preflight.py:197, manifest.py:196; trece recibos privados validados, contradicciones y booleanos rechazados |
| Transporte emparejado y privacidad | ✓ | LM/DiT tokens y metadata idénticos por comparación independiente, tests de privacidad conformes |
| Inferencia GPU/calidad | Pendiente | No se atribuye evidencia CPU a seis generaciones ni a escucha |

Suite dirigida independiente de nueve archivos: **271 passed, 1 skipped, 5 warnings**. Reproducción de progreso/cancelación y validación de trece recibos intactos. Recibo HTTP CPU leído, sin repetirlo ni presentarlo como GPU. **Sin defectos de corrección encontrados.**

## Fusión y límites

| ID | Grado | Gap | Tarea | Veredicto | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin hallazgos en el tramo CPU | T-16 | conforme para pasar a QA CPU | Tablas A/B, reproducciones y validadores independientes |

Cero Critical, Important o Minor pendientes, sin rebates. T-16 continúa en progreso; faltan QA independiente, seis tomas emparejadas, telemetría/descarga real y escucha privada. Ningún cambio de motor por defecto ni aprobación artística. Jira/Confluence desactivados. Consumo real desconocido, medición estimada; duración de reloj no se convierte en horas IA.
