# Revisión independiente de T-15 — intento 2

2026-10-05. Lentes A+B nuevas y de contexto fresco. Revisaron las correcciones frente a la tabla completa del [intento 1](review-attempt1.md), sin reabrir criterios aprobados ni inventar evidencia de GPU. No hubo escrituras de los revisores, generación ni modificaciones del ledger.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| R1: supervisión al 95 % del presupuesto conservador | Corregido | `run-comparison.py:57–119`; monitor de salud cada 2 s; fallo de lectura o presupuesto consumido invalidan la tanda. No se presenta el crecimiento agregado como spill observado. |
| Cancelación exclusivamente del job propio | Conforme | `run-comparison.py:183–201`, `cli-controlled-job.py:16–22`; reserva previa del ULID, DELETE de ese ID y comprobación final idle/unloaded. |
| R2: copia completa y procedencia verificadas | Corregido | `run-comparison.py:121–133,279–304`; duración real/formato, hash del MP3 y master, ganancia, checkpoint anterior al rename. |
| Referencia/manifiestos sin sobrescritura | Conforme | `run-comparison.py:314–329`; escritura exclusiva o verificación del hash existente. |
| Investigación, privacidad y parámetros fijos | Conforme, heredado | [Intento 1](review-attempt1.md); sin cambios que invaliden lo aprobado. |
| Alcance y TDD/cobertura n/a | Conforme | Scope exit 0, sin avisos/exclusiones de usuario; siete journals ajenos preservados; sin producto ni contratos cambiados. |
| Generación, normalización real y QA | Pendientes | No se declaran realizadas por esta revisión. |

Ambos agentes ejecutaron independientemente `fix1-cpu-probe.py` desde el entorno gestionado: exit 0, `ALL_FIX1_CPU_CHECKS_PASSED; GPU not executed`. La prueba reproduce presupuesto al 95 %, fallo del monitor y job ajeno; rechaza MP3 real de 10 s, acepta 90 s/48 kHz/estéreo y rechaza checkpoint ausente/hash incorrecto. AST 3.11 confirma el primer ULID reservado como ID del job.

Fusión: **0 Critical / 0 Important / 0 Minor pendientes**. R1 y R2 corregidos, sin rebates. C y D no aplican según selector; perfil investigación ausente, lente B genérica. La cadencia del monitor es muestreo, no garantía de observar picos entre muestras. Sigue pendiente la verificación efectiva de seis tomas y QA; no hay veredicto de calidad musical.
