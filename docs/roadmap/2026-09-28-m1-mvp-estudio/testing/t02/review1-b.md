**Veredicto B: ✗ — requiere correcciones.** Revisión estática del paquete INLINE y del diff de las 22 fuentes, incluidos ambos contratos y todos los cambios mostrados de `uv.lock`. No ejecuté pruebas ni comprobé hashes; las evidencias de ejecución y custodia pertenecen a raíz.

| Criterio | Resultado | Evidencia |
|---|:---:|---|
| Esquema inicial de 23 tablas, campos comunes y dependencias declaradas | ✓ | DDL, modelos y diff del lock suministrados |
| Lectura consistente de la proyección | ✓ | `snapshots.py:176`: transacción explícita; `db.py:42`: `BEGIN` real |
| FTS transaccional de canción activa y letra vigente | ✓ | `0001_initial.py:41`, `db.py:68` |
| DAG y protección de sujetos frente a purga física | ✓ | `initial_invariants.py:118`, `:126`, `:146` |
| Raíz canónica preservada por todas las mutaciones | ✗ | B-01 |
| Pertenencia a canción preservada al modificar sujetos del linaje | ✗ | B-02 |
| Snapshots restaurables con referencias globales compartidas | ✗ | B-03 |
| Fallos de una canción aislados durante reconciliación | ✗ | B-04 |
| Identificación de la última copia restaurable | ✗ | B-05 |
| Registro observable de fallos de persistencia | ✗ | B-06 |

| Gap | Gravedad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| B-01 | **Important** | `apps/server/app/migrations/initial_invariants.py:139` | La raíz solo se recalcula al modificar `lineage_edge`. Con dos takes originales A y B de la misma canción, SQL directo u ORM permite cambiar `A.root_id` a B sin ninguna arista: las FK y comprobaciones de pertenencia pasan. También permite sobrescribir la raíz de un hijo existente. La BD queda con una raíz incorrecta y `snapshots.validate()` rechaza su proyección en `snapshots.py:167`. |
| B-02 | **Important** | `apps/server/app/migrations/initial_invariants.py:117` | La comprobación de canción de los extremos solo se ejecuta al insertar/actualizar la arista. Crear artworks A y B asociados a la misma canción, sin otras referencias, y enlazarlos; después cambiar `B.song_id` a otra canción del mismo propietario. Los triggers de referencias ordinarias no comprueban las aristas polimórficas existentes y permiten confirmar linaje entre canciones. Afecta tanto a SQL directo como al ORM. |
| B-03 | **Important** | `apps/server/app/snapshots.py:210` | Dos canciones pueden compartir un personaje global cuyo `sheet_artwork_id` pertenece a la primera. Al proyectar la segunda, el cierre incorpora el artwork, su canción y sus hijos. `validate()` exige exactamente una canción en `:112` y rechaza la instantánea. Ocurre también si una colección compartida tiene portada asociada a otra canción. Son relaciones admitidas por el esquema; impiden publicar y restaurar proyectos válidos. |
| B-04 | **Important** | `apps/server/app/snapshots.py:295` | Una canción cuya proyección falle —por ejemplo, B-03— aborta todo `reconcile`. Tras un commit de otra canción, el único `except` exterior de `db.py:56` deja sin actualizar las canciones restantes. En el siguiente arranque, `main.py:32` propaga el mismo fallo y el backend no termina de arrancar. Un proyecto problemático bloquea la recuperación del conjunto. |
| B-05 | **Important** | `apps/server/app/backup.py:85` | `due()` considera válida cualquier copia con `integrity_check=ok`, aunque `foreign_key_check` falle o falte `song_fts`. Un archivo con nombre reconocido y fecha reciente, estructuralmente íntegro pero no restaurable por `restore_backup`, aplaza el siguiente backup. La selección de “última válida” aplica menos condiciones que publicación y restauración. |
| B-06 | **Minor** | `apps/server/app/db.py:58`; `apps/server/app/backup.py:156` | Los fallos de snapshots se envían a `logging.getLogger("studio")`, mientras el fichero configurado usa `studio.server.<hash>` con propagación desactivada: ese evento no llega al log configurado. Los fallos de backup sí usan ese logger, pero `backup.failed` no está en `SAFE_EVENTS` (`logging.py:10`) y se convierte en `[redacted]`. Se pierde la identificación del fallo que el README promete registrar. |

**Critical:** ninguno identificado. Los escenarios anteriores se deducen del código suministrado; requieren reproducción por raíz. El coste de escanear todas las tablas y canciones tras cada commit queda para la lente D, conforme al reparto solicitado.