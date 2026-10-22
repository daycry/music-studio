# Diagnóstico y lectura real de contadores Windows

La tercera sonda de sólo lectura identifica la RTX 5070 por DXGI y correlaciona su LUID exacto con la instancia agregada de PDH. Dos adaptadores enumerados; tres muestras válidas, todos los códigos collect/return/cstatus cero. Compartida: 85,46484375 MiB; dedicada: 1.343,484375 MiB durante estas muestras. [Recibo portable](windows-native-probe-receipt.json).

Se siguió `custom-agents:debug-root-cause`, fuera del gancho de tres QA rojas: reproducción mínima, aislamiento, hipótesis probada y corrección con regresión TDD por el implementer.

| Caso real | Reproducción y causa probada | Corrección |
|---|---|---|
| `IndexError` al localizar el objeto | Registro `Perflib/009/Counter`: 12.521 entradas; terminador vacío impar comprobado. DXGI ya funcionaba; el fallo era anterior a abrir la query PDH. | Retirar sólo ese terminador; rechazar catálogos impares no vacíos. |
| `localized_counter_unresolved` en Shared Usage | Dos índices ingleses válidos para Shared y Dedicated Usage. `PdhLookupPerfNameByIndexW` devuelve en ambos casos el mismo nombre localizado y estado cero. | Traducir todos los índices y exigir un único nombre distinto; rechazar traducciones contradictorias. |

Los tests RED con sus fechas/SHA figuran en el recibo. El implementer comunica las regresiones verdes; la sonda nativa posterior acredita la lectura real. Las dos reproducciones fallidas y la prueba de aliases se conservan, sin sobrescribirlas. Esta publicación no sustituye el informe final de implementación, la cobertura, revisión fresca o QA CPU.

No se cargó ningún modelo ni se abrió/controló una ventana. No se leyó contenido de navegador, modificaron permisos o alteraron servicios. Query propia cerrada en finally; proceso de sonda terminal. Fuentes iguales antes/después de la lectura. Los IDs de adaptador y trazas con rutas personales permanecen privados.

Esto resuelve la identidad y lectura del sensor en esta máquina. Falta calibración con Administrador de tareas, navegador visible acreditado, preflight actual y evidencia durante inferencia. La memoria compartida en reposo no es una afirmación de desbordamiento de un modelo; no hay RTF ni benchmark ejecutado y todos sus criterios siguen abiertos.

No se escribe gotcha ni índice en `docs/knowledge`: su ownership fue excluido expresamente por el propietario. Diagnóstico trazado aquí y en el ledger. TDD n/a para la sonda privada y prosa; las correcciones de producto sí tienen sus RED de regresión.
