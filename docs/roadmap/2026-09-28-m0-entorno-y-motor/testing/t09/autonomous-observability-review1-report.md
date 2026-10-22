# Revisión de dos lentes — intento 1: observabilidad autónoma T-09 y documentación T-20

Lentes **A+B+D**, tres contextos frescos terminales. C no aplica por selector oficial automático; D se activa por esperas bloqueantes. Resultado: **0 Critical / 5 Important / 0 Minor**. Los cinco gaps requieren corrección antes de QA y piloto.

Se leyeron ocho archivos de código y doce documentos completos mediante diffs por archivo. Root verificó64 fuentes y12 documentos sin deriva. Scope exit0, sin avisos, información de exclusiones ni código excluido por el usuario. Los originales de los diffs se conservan; la copia legible normaliza sólo terminadores.

| Criterio | Resultado |
|---|---|
| O1: método explícito, política previa sellada e identidad/estados/unidades de GPU | Conforme CPU |
| O1: frescura de operaciones ligada a la muestra | Gap R09-O1 |
| O1: originales pertenecientes a la sesión/plan declarados | Gap R09-O2 |
| O1: reanudación con baseline fresco | Gap R09-O3 |
| O1: re-acreditación tras pausa preservando historia | Gap R09-O4 |
| O1: cadencia de monitorización | Gap R09-O5 |
| O1: navegador, contraste dedicado y confianza shared explícita | Conforme CPU; piloto real pendiente |
| T-09: matriz160, GPU, RTF, recomendación y calidad | No verificables en esta revisión CPU; tarea abierta |
| T-20: Docker/Ollama compartido, SQLite y requisitos futuros coherentes | Tres criterios documentales conformes A+B; no despliegue acreditado |
| Alcance, constitución y evidencia TDD/cobertura | Conformes; coverage oficial80,80% de archivos cambiados, no diff-lines |
| Exports/OpenAPI | No aplican al delta |

## Gaps y evidencia

| ID | Origen | Grado | Fichero:línea | Defecto |
|---|---|---|---|---|
| R09-O1 | A1-01 | Important | `scripts/eval/benchmark_observation.py:125` | La fecha general actualizada permite aceptar operaciones PDH/NVML antiguas; enlazar sustantivamente brackets y FILETIMEs a la muestra. |
| R09-O2 | B1-01 | Important | `scripts/eval/benchmark_observation.py:414` | Originales de otra sesión pasan al cambiar conjuntamente context y plan; ligar originales de adquisición a session/plan/source/image/lock/policy. |
| R09-O3 | B1-02 | Important | `scripts/eval/benchmark.py:369` | Resume valida frescura del baseline histórico antes de observar el nuevo y falla tras900s aun con continuidad fresca. |
| R09-O4 | B1-03 | Important | `scripts/eval/benchmark_observation.py:497` | Una acreditación nueva falla al conservar muestras anteriores a su recuperación; segmentar continuidad y acreditaciones preservando la historia. |
| R09-O5 | D-01 | Important | `scripts/eval/benchmark_observation.py:561` | Esperar1s además del coste de muestreo1,6s produce gap2,602s y aborta sensores válidos; respetar periodo sin sumar espera fija. |

A ejecutó siete tests dirigidos:7passed/0,23s, y reprodujo lecturas de hace1000,1s aceptadas al actualizar sólo timestamp/monotonic general. B ejecutó reproducciones CPU: control y originales prestados aceptados, continuidad fresca aceptada; baseline histórico en resume rechazado, piloto nuevo aceptado solo y rechazado con historia anterior conservada. D reprodujo una operación propia5s con muestra1,6s y gap2,602s (+62,5%); el fallo fue observability_lost_auto_replayed_or_paused_sample. Son datos sintéticos de pruebas, no mediciones GPU.

No se suman los siete tests de A a los135 de implementación ni las sondas solapadas. El coste del validador acumulado medido por D (30.000 muestras sintéticas≈0,499s) no acreditó degradación material y no se abre gap por microoptimización.

A marcó el chequeo general de originales como conforme; la reproducción más específica de B demuestra el hueco de pertenencia a sesión y prevalece en R09-O2. No hay rebates ni deuda aceptada. Las revisiones1–5 de la subfase anterior se conservan; estos cinco defectos pertenecen al delta ADR-0036. T-20 permanece en revisión hasta QA documental y su verificación de cierre. Root controla ledger, Git y publicación.

La sonda root de tres consultas nativas acredita ABI/metadatos de Windows, sin calibración física. No hubo modelos, UI, Docker o GPU nueva en las lentes. Siguiente: fix TDD concreto → revisión intento2 con traspaso completo → QA → piloto real → matriz160.
