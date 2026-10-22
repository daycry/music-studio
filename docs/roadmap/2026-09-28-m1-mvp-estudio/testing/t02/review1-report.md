# T02 — Revisión1 A/B/C/D

Cuatro contextos frescos, lectura estática de paquete INLINE exacto. Root coteja22fuentes y originales; revisores no ejecutaron tests ni hashes. Scope oficial0sinavisos/exclusiones; C/D seleccionadas por SQL y consultas/migraciones.

CeroCritical, ochoImportant y unMinor; A/B deduplicados. Todos pendientes de verificar mediante reproducción antes de corregir; sin rebates ni reset de contador. T02 vuelve a en-progreso.

| ID | Grado | Hallazgo | Lentes | Evidencia |
|---|---|---|---|---|
| R02-01 | Important | Raíz canónica modificable fuera de cambios de aristas | A-G1/B01 | initial_invariants.py:139 |
| R02-02 | Important | Mover sujeto deja linaje cruzado entre canciones | A-G2/B02 | initial_invariants.py:117 |
| R02-03 | Important | Referencias globales a artwork de otra canción rompen snapshot | A-G3/B03 | snapshots.py:210 |
| R02-04 | Important | Una proyección fallida aborta reconciliación y arranque | B04 | snapshots.py:295 |
| R02-05 | Important | due acepta backup no restaurable y aplaza copia válida | B05 | backup.py:85 |
| R02-06 | Minor | Eventos de errores no llegan identificables al logger configurado | B06 | db.py:58 / backup.py:156 |
| R02-07 | Important | Cada commit escanea y publica toda la biblioteca | D01 | db.py:55 / snapshots.py:175 |
| R02-08 | Important | Cada arista recalcula todos los takes incluso ajenos | D02 | initial_invariants.py:139 |
| R02-09 | Important | Borrado FTS por columna UNINDEXED escanea biblioteca | D03 | 0001_initial.py:44 |

Las magnitudes de D son análisis de complejidad, no tiempos medidos. No cambiar contratos/globals/IDs para hacer pasar casos sin decidir semántica. Referencias compartidas requieren diseño focalizado antes del fix. QA independiente posterior; no aceptar biblioteca privada/M03/M0/M1 ni Git.
