**Lente D · intento 3/3: ✗ — un hallazgo nuevo Important introducido por fix2.** Revisión estática del paquete INLINE; sin herramientas, pruebas ni comprobaciones propias de hashes. Los resultados de ejecución citados pertenecen a raíz.

| Criterio | ✓/✗ | Evidencia y evaluación |
|---|:---:|---|
| R02-15: consultas del cierre por lotes y reutilización de filas | ✓ | `closure_rows.py:30,51` agrupa consultas en lotes de 400 y conserva filas/resultados. Raíz aporta 25→25 SELECT con 20→200 takes. |
| R02-16: búsquedas y clasificación en memoria | ✓ | `closure_rows.py:82`; `snapshots.py:267,305,344`: índices de relaciones, caché de pertenencia y conjunto de identidades primarias eliminan los escaneos señalados. |
| R02-17: comprobar desde la última copia válida | ✓ | `backup.py:83–108` termina al encontrarla; `:154–156` evita repetir inmediatamente `initial()`. Con 14 copias válidas abre una, según evidencia aportada. |
| R02-14: cancelación durante copia de candidatos bloqueados | ✓ | `backup.py:93–103,203`: timeout cero y callback por página; `InterruptedError` no se captura como candidato inválido. |
| R02-07: coste de publicación de raíces pendientes | ✓ | `snapshots.py:519–530` conserva publicación acotada; el cierre usa lotes e índices. Evaluación exclusivamente de rendimiento; la corrección concurrente corresponde a A/B. |
| Evitar consultas repetidas durante restauración | ✗ | Fix2 añade una consulta individual por fila y después repite esa misma lectura dentro de la misma transacción. |

| Hallazgo | Grado | Fichero:línea | Escenario concreto y magnitud |
|---|---|---|---|
| D3-01 — Prevalidación de colisiones duplica las lecturas individuales | **Important** | `apps/server/app/snapshots.py:564` y `:588` | Restaurar una canción con **405 takes y 810 assets**, volumen incluido en el paquete, añade **al menos 1.215 SELECT** para esas dos tablas en la prevalidación. El bucle de inserción vuelve a consultar las mismas 1.215 identidades: **al menos 2.430 SELECT**, frente a 1.215 antes de fix2, además de análisis, aristas y otras entidades. Las segundas lecturas ocurren tras iniciar escrituras en `snapshot_import`, prolongando la transacción que ocupa el único escritor SQLite. Es trabajo evitable: conservar los resultados de la prevalidación y recuperarlos por lotes permite comprobar todas las colisiones antes de abrir la excepción sin repetir consultas por fila. |

**Critical: 0 · Important: 1 · Minor: 0.**

R02-15, R02-16 y R02-17 muestran corregidos sus escenarios originales; R02-14 muestra corregida su parte de cancelación. D3-01 es un defecto nuevo del delta de restauración, no una reapertura de esos escenarios. Se conservan los IDs y el contador anteriores; la adjudicación final, QA y aceptación de T02/M-03/Git corresponden a raíz.