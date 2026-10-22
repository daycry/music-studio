# T02 — Revisión de dos lentes, intento2/3

Las cuatro lentes independientes terminan exit0. A/B/C/D revisaron estáticamente el diff completo, deltafix1 y25fuentes; no ejecutaron pruebas propias. Los originales y paquetes quedan sellados por raíz. Las copias añadidas idénticas se suministraron como fuente completa; no se omitieron hunks antiguos. Transporte inicial falló antes de producir veredicto; sus originales se conservan y no consumen otro intento.

Resultado fusionado:0Critical/8Important/0Minor. Coinciden A/B en selección, soporte y carrera; la cancelación de B y la parte de cancelación de D comparten ID. Los ocho escenarios deben reproducirse antes de corregir o rebatir con evidencia. C no encontró seguridad introducida. R02-01..06/08/09 muestran corrección de los escenarios anteriores; R02-07 continúa parcialmente abierto por corrección concurrente y coste del cierre. No se borran los nueve IDs ni se acepta T02/QA/M03/Git.

| ID | Grado | Lentes | Gap | Evidencia estática | Estado |
|---|---|---|---|---|---|
| R02-10 | Important | B2-01 | Pertenencia ordinaria transitiva | `fix1_invariants.py:116`: Mover shot/video_project puede dejar job_id de una versión en otra canción. | Pendiente reproducción |
| R02-11 | Important | A-G3/B2-02 | Selección de versión de otro plano | `snapshots.py:304`: current_version_id debe pertenecer a ese shot, además de la canción. | Pendiente reproducción |
| R02-12 | Important | A-G2/B2-03 | Contenido de soporte editable | `fix1_invariants.py:31`: La guarda song no cubre rating/text/prompt ni otros hijos del soporte. | Pendiente reproducción |
| R02-13 | Important | A-G1/B2-04 | Dependencia nueva no invalida consumidor | `snapshots.py:415`: Cambio entre lectura del cierre nuevo y registro de membresía puede limpiar JSON obsoleto. | Pendiente reproducción |
| R02-14 | Important | B2-05/D2-03 parcialmente | Cancelación omitida al comprobar backups | `backup.py:91`: origin.backup de candidatos no recibe progress; close espera mientras existe bloqueo. | Pendiente reproducción |
| R02-15 | Important | D2-01 | Consultas por cada fila del cierre | `snapshots.py:80,100,364,373`: 200 takes requieren al menos800SELECT en esa parte; es conteo estático, no latencia. | Pendiente reproducción |
| R02-16 | Important | D2-02 | Validación cuadrática en memoria | `snapshots.py:319,326,333`: lookup escanea assets/aristas por cada identidad y selección primaria escanea cada tabla. | Pendiente reproducción |
| R02-17 | Important | D2-03 | Comprobación de toda la retención | `backup.py:81,85,91,92`: Cada hora copia/valida todos los candidatos incluso si el más reciente es válido. | Pendiente reproducción |

Originales completos: [A](review2-a.md), [B](review2-b.md), [C](review2-c.md), [D](review2-d.md).
