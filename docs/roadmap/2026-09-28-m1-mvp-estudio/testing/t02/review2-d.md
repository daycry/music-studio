**Veredicto D: ✗ — 3 hallazgos Important.** Revisión2/3 estática del diff completo, fix1 y las 25 fuentes INLINE, considerando ambos paths de cada schema idéntico y todos los bloques cambiados del lock. Sin herramientas, tests ni comprobación propia de hashes. Las magnitudes siguientes son conteos y complejidad deducidos del código, no latencias medidas.

| Criterio D | Resultado | Evidencia |
|---|:---:|---|
| Publicar únicamente raíces pendientes | ✓ | `snapshots.py:502` utiliza dirty; `0002_snapshot_metadata.py:25` añade el índice correspondiente. |
| Evitar consultas por cada fila del cierre | ✗ | D2-01: consultas individuales y recuperación repetida de filas. |
| Evitar recorridos repetidos del documento | ✗ | D2-02: validación cuadrática dentro de cada publicación. |
| Recalcular únicamente takes afectados con raíz diferente | ✓ | `fix1_invariants.py:111–114` restringe descendientes y diferencias. |
| Localizar entradas FTS por identidad indexada | ✓ | `fix1_invariants.py:161,180`: rowid y conjunto OLD/NEW. |
| Ejecutar migraciones y backup fuera del event loop | ✓ | `main.py:26,32`; `backup.py:145,162`. |
| Acotar trabajo y memoria de comprobación periódica | ✗ | D2-03: copia y validación de todos los backups cada hora. |

| Hallazgo | Gravedad | Fichero:línea | Escenario concreto y magnitud |
|---|---|---|---|
| **D2-01 — N+1 en la proyección del cierre** | **Important** | `apps/server/app/snapshots.py:80`, `:100`, `:364`, `:373` | Una canción con **200 takes** exige, sólo para esos takes, **800 SELECT**: fetch individual, búsqueda de analysis, assets y linaje por take. Se añaden consultas para jobs, assets, aristas y demás identidades. Los lookup recuperan filas completas, pero conservan únicamente su ID para volver a recuperarlas mediante fetch. Cambiar una valoración vuelve a ejecutar todo este trabajo antes de retornar del callback síncrono (`db.py:65`). El coste de consultas crece con cada fila del proyecto; los índices y la igualdad de 85 SELECT con 1/41 raíces no comprueban este eje de crecimiento. |
| **D2-02 — Validación del cierre mediante escaneos cuadráticos** | **Important** | `apps/server/app/snapshots.py:319`, `:326`, `:333` | Cada identidad visitada vuelve a recorrer íntegramente `union["asset"]` y `union["lineage_edge"]`; cada clasificación de sección vuelve a buscar linealmente el ID en su tabla primaria. Con **200 takes y 400 assets** —master/listen—, sólo las búsquedas de assets para esas **600 identidades** examinan **240.000 filas**, aunque todas las relaciones ya están presentes en el documento. Las comprobaciones de sección de los 400 assets suman **80.200 comparaciones** cuando todos son primarios. El coste es **O(R·(A+E) + ΣNtabla²)**. Se ejecuta en cada `publish` (`:416`), incluso al cambiar una sola valoración, y para cada consumidor de un recurso global. Este recorrido del cierre en memoria es nuevo en fix1. |
| **D2-03 — Relectura completa de toda la retención cada hora** | **Important** | `apps/server/app/backup.py:81`, `:85`, `:91`, `:92` | Con **14 copias de 256 MiB**, cada comprobación horaria copia aproximadamente **3,5 GiB** a SQLite en memoria y ejecuta integridad, FK y FTS sobre todas ellas, aunque la copia más reciente sea válida y no corresponda crear otra. Son aproximadamente **84 GiB diarios de copiado lógico**, más los recorridos de validación. La memoria temporal crece con el tamaño completo de una copia. `initial()` y el primer ciclo de `run()` repiten inmediatamente esta comprobación. Además, `origin.backup(connection)` no recibe el callback de cancelación: durante este recorrido, el hilo propio continúa trabajando y `close()` espera su terminación. Validar candidatos desde el más reciente hasta encontrar uno válido evita recorrer necesariamente toda la retención. |

**Seguimiento de los nueve IDs previos**

| ID | Evaluación estática de fix1 | Evidencia |
|---|---|---|
| R02-01 | Corrección observable del escenario original; cierre funcional corresponde a A/B. | `fix1_invariants.py:94`: guardas INSERT/UPDATE de raíz. |
| R02-02 | Corrección observable del movimiento original de artwork; cierre integral corresponde a A/B. | `fix1_invariants.py:116–136`: validación inversa y sujetos transitivos. |
| R02-03 | Corrección observable de los dos ejemplos originales; cierre integral corresponde a A/B. | `snapshots.py:95,384`: soporte separado y expansión de hijos limitada a la raíz. |
| R02-04 | Corrección observable del fallo individual original; cierre funcional corresponde a A/B. | `snapshots.py:484,511`: captura por canción en auditoría y publicación. |
| R02-05 | Corrección observable de los daños originales; **nuevo coste D2-03**. | `backup.py:23,92,121`: validador compartido. |
| R02-06 | Corrección observable del registro original; cierre corresponde a B. | `db.py:15,39,68`; `backup.py:17,154`. |
| **R02-07** | **Corrección parcial; permanece abierto en D.** Desaparece la publicación de toda la biblioteca, pero D2-01/D2-02 mantienen costes evitables por cada cierre afectado. | `snapshots.py:502` frente a `:364,319,335`. |
| **R02-08** | **Resuelto en D para el defecto original.** Las aristas ajenas a takes no seleccionan descendientes; sólo se actualizan raíces diferentes de takes afectados. | `fix1_invariants.py:107–114`. |
| **R02-09** | **Resuelto en D.** Retirada FTS por rowid indexado; OLD/NEW se procesan como conjunto de IDs distintos. | `fix1_invariants.py:145,161,176–181`. |

**Critical: 0 · Important: 3 · Minor: 0.** Los IDs y veredictos anteriores se conservan; esta lente no acredita QA ni aceptación de T02/M-03/M1.