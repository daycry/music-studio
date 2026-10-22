**Veredicto: requiere cambios.** Tres gaps **Important** de rendimiento en M1/T02.

Revisión estática del diff y las 22 fuentes del paquete INLINE, incluidas ambas copias de los schemas y todos los cambios mostrados de `uv.lock`. Las pruebas y hashes aportados son evidencia de raíz; no ejecuté comprobaciones propias.

| Criterio D | Resultado | Evidencia |
|---|---|---|
| Consultas dentro de bucles con volumen variable | ✗ | `snapshots.py:180,294`: 20 lecturas completas por canción en cada reconciliación. |
| Trabajo repetido evitable tras mutaciones | ✗ | `db.py:55`: cualquier commit de Session reconcilia toda la biblioteca. |
| Complejidad de mantenimiento del linaje | ✗ | `initial_invariants.py:139`: cada arista actualiza todos los takes. |
| Acceso eficiente para mantenimiento FTS | ✗ | `0001_initial.py:44,53`: borrado por columna FTS `UNINDEXED`. |
| Migraciones y backup fuera del event loop | ✓ | `main.py:26,32` y `backup.py:147,164`: trabajo delegado a hilos. Los bucles de creación de DDL tienen tamaño fijo. |

| Gap | Gravedad | Fichero:línea | Escenario de carga y magnitud |
|---|---|---|---|
| D-01 | **Important** | `apps/server/app/db.py:55`; `apps/server/app/snapshots.py:175,291` | Con **1.000 canciones y 30.000 filas** en las 20 tablas proyectadas, cambiar una valoración dispara **20.001 SELECT**, materializa aproximadamente **30 millones de filas** y publica **1.000 JSON con 1.000 fsync**, aunque afecte a una sola canción. Además, cada proyección repite escaneos para cerrar referencias y ordena tablas completas. Coste mínimo **O(S·N)** por commit, cuadrático respecto a canciones si mantienen un tamaño medio fijo. El callback es síncrono: retiene al llamador hasta terminar; si este confirma desde una coroutine, bloquea también el event loop. No hay una ruta de negocio en este paquete que permita afirmar que ese bloqueo HTTP ya ocurre. |
| D-02 | **Important** | `apps/server/app/migrations/initial_invariants.py:139` | Con **10.000 takes**, insertar **100 aristas** ejecuta **un millón de actualizaciones de take**, con CTE de ancestros y triggers de UPDATE para cada fila, incluso para canciones ajenas y raíces que no cambian. También ocurre al modificar una arista de artwork o personaje. El trabajo mantiene ocupado al escritor SQLite durante toda la transacción; una edición local escala con toda la biblioteca. |
| D-03 | **Important** | `apps/server/app/migrations/versions/0001_initial.py:39,44,53` | `song_id` es `UNINDEXED` en FTS5 y los triggers eliminan mediante `WHERE song_id=…`, sin utilizar `rowid` para localizar la entrada. Con **5.000 canciones activas**, actualizar **100 canciones** implica aproximadamente **500.000 comprobaciones de filas FTS** para retirar 100 entradas. Actualizar 100 versiones de letra ejecuta dos borrados por UPDATE, incluso cuando `OLD.song_id = NEW.song_id`: aproximadamente **un millón de comprobaciones**. El coste se añade dentro de la transacción de escritura. |

Para resolverlos: publicar únicamente los cierres afectados por cada commit, consultar o reutilizar datos sin releer toda la biblioteca por canción, recalcular raíces solo para descendientes afectados y localizar las entradas FTS mediante un `rowid` estable o una correspondencia indexada.

**Critical: ninguno. Minor: ninguno.** Las magnitudes anteriores se deducen del código; no son tiempos medidos.