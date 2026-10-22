**Veredicto: ✗ — 3 gaps Important de conformidad.** Lectura estática del diff y las 22 fuentes INLINE; pruebas, hashes y cobertura se atribuyen exclusivamente a raíz.

| T-02 → criterio | Resultado | Evidencia |
|---|---|---|
| 23 tablas, campos comunes, usuario `local`, nullabilidad y defaults | ✓ | DDL completo y modelos cotejados con `datos.md`; usuario autorreferente en `0001_initial.py:28`. |
| WAL y FK por conexión | ✓ | `db.py:33`; test de dos conexiones en `test_schema_t02.py:70`. |
| FTS transaccional sobre canción activa y letra vigente | ✓ | `0001_initial.py:38`; tests de selección, actualización, papelera, restauración, rollback y reconstrucción. |
| Snapshot regenerable y reconstrucción completa | ✗ | G3: referencias globales válidas pueden impedir publicar el snapshot. |
| Backup diario, WAL/FTS, restauración, retención y última copia válida | ✓ | Implementación y evidencia suministrada de raíz; periodicidad con reloj simulado, sin atribuir espera real de 24 h. |
| Linaje derivado y raíz correcta | ✗ | G1: escritura directa de `root_id` permite una raíz no canónica. |
| Varios padres y pertenencia coherente | ✗ | G2: mover un extremo permite invalidar un linaje ya existente. |
| Papelera conserva hijos; purga protege referencias | ✓ | FK sin cascadas y protección polimórfica en `initial_invariants.py:144`. |
| Tests por criterio y cobertura | ✓ | Tests leídos; evidencia raíz: **793/838 = 94,63 %**, módulos propios ≥80 %, sin exclusiones. Los escenarios G1–G3 carecen de prueba específica. |
| Alcance declarado frente al plan | ✓ | 22 archivos dentro del alcance; helpers, recursos empaquetados, contratos y lifespan corresponden a T-02. |
| Constitución explícita | ✗ | G2 incumple pertenencia coherente a canción, `docs/CONSTITUTION.md:10`. |
| Verificación ejecutada y cierre honesto | ✓ | Ledger `tasks.md:126` y salida suministrada: ciclos Alembic exit 0; 27 passed/206 deselected. T-02 continúa `en-progreso`; M-03 permanece pendiente. |
| Generado/descrito actualizado | ✗ | README afirma DAG/proyección completa; G2–G3 impiden sostener esas garantías para todos los estados permitidos. Interop no aplica: no cambia `commands/`, `agents/` ni `hooks/`. |

| Gap | Gravedad | Fichero:línea | Escenario e incumplimiento |
|---|---|---|---|
| G1 | **Important** | `apps/server/app/migrations/initial_invariants.py:139` | La raíz se recalcula únicamente al modificar `lineage_edge`. Insertar un take original con `root_id` apuntando a otro take de la misma canción, o actualizar la raíz de un hijo existente a sí mismo, supera FK y comprobaciones de propietario/canción. SQLite conserva una raíz incorrecta y `snapshots.validate` después rechaza su proyección (`snapshots.py:167`). Incumple raíz propia/canónica de ADR-0041:16 y el criterio `tasks.md:119`. |
| G2 | **Important** | `apps/server/app/migrations/initial_invariants.py:93` | La validación inversa recorre solo referencias de `initial_relations.json`; los extremos polimórficos de `lineage_edge` no figuran ahí. Crear dos takes de A unidos por linaje y mover ambos —junto con sus referencias ordinarias necesarias— a B puede ser coherente; **mover solo uno**, adaptando su job y raíz, deja una arista A↔B sin volver a ejecutar `lineage_validate`. La validación de extremos solo ocurre al escribir la arista (`:117`). Incumple ADR-0041:16 y Constitución:10. |
| G3 | **Important** | `apps/server/app/snapshots.py:209` | Un personaje global tiene `sheet_artwork_id` de una portada de A y se usa en un vídeo de B; también puede ocurrir con una colección cuya portada pertenece a A y contiene B. Son relaciones permitidas por el esquema y el diseño de bibliotecas globales. `project(B)` sigue la FK hasta artwork y canción A, incorpora sus hijos y produce más de una canción. `validate` lo rechaza en `:112`. Tras commit, B queda sin snapshot actualizado; al reiniciar, la reconciliación propaga el error y aborta el lifespan (`main.py:32`). Incumple snapshot completo con referencias globales necesarias, `database-design.md:13`. |

**Critical: ninguno. Minor: ninguno.** Los gaps son escenarios deducidos del código, sin ejecución propia. OpenAPI no aplica: el diff contiene JSON Schema, ninguna spec OpenAPI. El coste de escanear todas las tablas y canciones por commit queda para la lente D; esta lente A no emite una conclusión de rendimiento.