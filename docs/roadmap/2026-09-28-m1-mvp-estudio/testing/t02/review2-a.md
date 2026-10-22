**Veredicto Lente A, revisión 2/3: ✗ — tres gaps Important.** Lectura estática del paquete INLINE, diff completo y delta Fix1. No ejecuté herramientas, tests ni hashes. Las ejecuciones y la custodia citadas pertenecen a raíz.

| T-02 → criterio | Resultado | Evidencia |
|---|:---:|---|
| 23 tablas, campos comunes, usuario `local`, defaults y nullabilidad | ✓ | Modelos y DDL cotejados con `datos.md`; baseline inicial conservado. |
| WAL y FK por conexión | ✓ | `db.py:43`; prueba de dos conexiones en `test_schema_t02.py:70`. |
| FTS transaccional, canción activa y letra vigente | ✓ | `fix1_invariants.py:140`; selección, papelera, rollback y reconstrucción cubiertos por tests leídos. |
| Snapshot regenerable, restaurable y con referencias globales | ✗ | G1: la invalidación puede perder un cambio concurrente de una dependencia recién incorporada. |
| Soporte durable y no editable hasta promoción | ✗ | G2: únicamente se protege la fila `song`, no su contenido dependiente. |
| Selecciones y pertenencia coherentes al importar | ✗ | G3: `shot.current_version_id` admite una versión de otro plano de la misma canción. |
| Raíz canónica y varios padres | ✓ | Guardas INSERT/UPDATE y recomputación acotada OLD/NEW en `fix1_invariants.py:89`. |
| Papelera conserva hijos; purga protege referencias | ✓ | FK diferidas sin cascadas y guardas polimórficas en `initial_invariants.py:144`. |
| Backup nativo diario, WAL/FTS, restauración y rotación | ✓ | Validación común en `backup.py:23`; pruebas leídas de restauración, concurrencia y conservación de copia previa. |
| Tests y cobertura | ✓ | Evidencia de raíz: **978/1020 = 95,88 % de ocho módulos completos**, mínimo 91,59 %, cero exclusiones. **No es cobertura del diff.** Los tres escenarios siguientes no están cubiertos. |
| Alcance frente al plan | ✓ | Los 25 archivos declarados corresponden a persistencia, contratos, empaquetado, lifespan y tests de T-02. Scope aportado sin avisos ni exclusiones. |
| Constitución explícita | ✓ | No identifico una infracción adicional demostrable de un principio explícito. Los gaps siguientes incumplen requisitos del diseño aprobado. |
| Verificación ejecutada y cierre honesto | ✓ | Evidencia aportada: seis ciclos exit 0 y selección exacta **29 passed / 236 deselected**. Ledger: `en-revision`, criterios abiertos; M-03 y aceptación final pendientes. |
| Generado y descrito actualizado | ✗ | README:98–103 afirma invalidación durable de consumidores; G1 impide sostener esa garantía. Contratos duplicados actualizados según custodia de raíz. |

Interop **no aplica**: el diff no toca `commands/`, `agents/` ni `hooks/`. OpenAPI **no aplica**: los contratos incluidos son JSON Schema.

| Gap | Gravedad | Fichero:línea | Escenario concreto e incumplimiento |
|---|---|---|---|
| G1 | **Important** | `apps/server/app/snapshots.py:415`; `apps/server/app/migrations/fix1_invariants.py:62` | B incorpora una colección C cuya portada pertenece a A. El commit invalida B, pero su membresía publicada todavía no contiene C ni la portada. El publicador captura generación G y proyecta la nueva dependencia. Antes de registrar esa membresía, otra transacción cambia `C.name`. El trigger busca consumidores en la membresía anterior y no incrementa la generación de B; C no tiene canción propia. El publicador publica el nombre antiguo y limpia `dirty` porque sigue viendo G. B queda **limpia con JSON obsoleto** hasta la auditoría de otro arranque. Incumple ADR-0044:22–24: todos los consumidores e intercalaciones deben conservar reparación pendiente. El test de carrera existente cambia la propia canción, cuya invalidación sí está garantizada. |
| G2 | **Important** | `apps/server/app/migrations/fix1_invariants.py:31` | Tras importar B con A como soporte, SQL/Core/ORM puede modificar `lyrics_version.text`, `take.rating` o `artwork.prompt` pertenecientes a A sin promoverla. `support_song_edit` sólo protege UPDATE de `song`; los triggers de esas entidades validan relaciones e invalidan snapshots, pero no rechazan edición de contenido de soporte. Esto permite alterar historia importada y puede provocar una colisión al importar después el proyecto completo original de A. Incumple ADR-0044:18: «Su contenido no se modifica mediante acciones ordinarias de proyecto». El test de soporte sólo intenta cambiar `song.title`. |
| G3 | **Important** | `apps/server/app/snapshots.py:301`; `apps/server/app/migrations/initial_invariants.py:92` | Una canción tiene planos P y Q; V pertenece a Q. Cambiar `P.current_version_id=V.id` pasa la comparación de pertenencia porque P y V tienen la misma canción. La validación de timeline tampoco comprueba esa selección. El documento puede validarse y restaurarse con P seleccionando una versión de Q; las guardas SQL comparan igualmente canción y propietario, no `V.shot_id == P.id`. Incumple la selección de versión propia de `shot` en `datos.md:109` y las referencias reales/coherentes exigidas por `database-design.md:17`. |

Evaluación independiente de los nueve IDs anteriores:

| ID | Resultado tras Fix1 | Evidencia estática |
|---|---|---|
| R02-01 | **Resuelto** | Guardas canónicas de INSERT/UPDATE de take, `fix1_invariants.py:94`; regresión directa y ORM leídas. |
| R02-02 | **Resuelto** | Validación inversa de extremos y movimientos transitivos, `fix1_invariants.py:116`. |
| R02-03 | **Resuelto en sus escenarios originales** | Cierre dirigido, dependencias separadas y ambos round-trips globales. G2/G3 son gaps adicionales de las garantías de soporte/selección. |
| R02-04 | **Resuelto** | Aislamiento por raíz y auditoría de arranque, `snapshots.py:474`; pruebas de fallo individual y lifespan leídas. |
| R02-05 | **Resuelto** | Creación, selección y restauración comparten `validate_database`, `backup.py:23`. |
| R02-06 | **Resuelto** | Registro de eventos seguros desde módulos T02 y uso del logger configurado; prueba de fichero real leída. |
| R02-07 | **Reabierto parcialmente** | Se elimina la proyección de toda la biblioteca, pero G1 deja incompleta la invalidación durable exigida por ADR-0044. Los 85 SELECT aportados no prueban esta intercalación. |
| R02-08 | **Resuelto** | Recomputación sólo de descendientes take afectados y raíces distintas, `fix1_invariants.py:107–114`. |
| R02-09 | **Resuelto** | Correspondencia estable e indexada por rowid; OLD/NEW de letras mediante conjunto de IDs, `fix1_invariants.py:175`. |

**Critical: 0 · Important: 3 · Minor: 0.** Los escenarios son deducciones del código, pendientes de reproducción por raíz. Este veredicto conserva revisión1 y sus IDs; no acredita QA, cierre de T-02, M-03 ni integración Git.