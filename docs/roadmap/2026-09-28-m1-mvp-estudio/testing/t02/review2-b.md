**Veredicto Lente B, revisión 2/3: ✗ — requiere correcciones.** Inspección estática del diff completo, delta fix1 y fuentes INLINE, incluidas ambas rutas de los contratos duplicados y los bloques cambiados del lock. No ejecuté herramientas, tests ni comprobaciones de hashes; la evidencia nativa indicada pertenece a raíz.

| Criterio | Resultado | Evidencia |
|---|:---:|---|
| Esquema, WAL/FK y lectura consistente de proyecciones | ✓ | `db.py:43–52`; migraciones y modelos suministrados |
| Raíz canónica ante escrituras directas y cambios de aristas | ✓ | `fix1_invariants.py:89–114` |
| Pertenencia coherente ante movimientos transitivos | ✗ | B2-01 |
| Cierre dirigido y referencias globales legales | ✓ | `snapshots.py:71–116`, `:291–349` |
| Selecciones coherentes dentro de las unidades importadas | ✗ | B2-02 |
| Protección del contenido de soporte hasta promoción | ✗ | B2-03 |
| Invalidación durable durante publicaciones concurrentes | ✗ | B2-04 |
| Aislamiento de errores ordinarios de proyección | ✓ | `snapshots.py:484–517` |
| Validación uniforme de copias candidatas y restauración | ✓ | `backup.py:23–30`, `:92`, `:121` |
| Cancelación de todo el trabajo del hilo de backup | ✗ | B2-05 |
| Eventos de fallo identificables en el logger configurado | ✓ | `db.py:15`, `:39`, `:68`; `backup.py:17`, `:154` |
| Actualizaciones acotadas de raíces y mantenimiento FTS por identidad | ✓ | `fix1_invariants.py:111–114`, `:145–184` |

| Hallazgo | Grado | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| **B2-01 — Movimiento transitivo deja referencias ordinarias cruzadas** | **Important** | `apps/server/app/migrations/fix1_invariants.py:116`; `apps/server/app/migrations/initial_invariants.py:92` | Un `shot` de un vídeo de A tiene una `shot_version` cuyo `job_id` pertenece a A. Con `current_version_id=NULL` y sin aristas, mover el shot a un vídeo de B cambia transitivamente la pertenencia de su versión a B. El trigger original sobre shot comprueba las relaciones directas; el nuevo trigger revisa exclusivamente linaje. Ninguno revalida `shot_version.job_id`. Se confirma una versión de B referida a un job de A y su snapshot falla después en `snapshots.py:309`. |
| **B2-02 — La versión seleccionada puede pertenecer a otro shot de la misma canción** | **Important** | `apps/server/app/snapshots.py:304`; `apps/server/app/migrations/initial_invariants.py:92` | Dos shots distintos del mismo vídeo tienen versiones propias. Asignar a `shot.current_version_id` la versión del otro shot pasa las comprobaciones porque ambas pertenecen a la misma canción. También pasa la validación de importación: compara canción, pero no `selected_version.shot_id == shot.id`. Se restaura y publica una selección ajena al historial del shot. |
| **B2-03 — El contenido de soporte sigue siendo editable** | **Important** | `apps/server/app/migrations/fix1_invariants.py:31` | Tras importar B con A como soporte, una Session puede actualizar normalmente `Take.rating`, `LyricsVersion.text` o `Artwork.prompt` de A. La protección instalada sólo cubre UPDATE de la fila `song`; los hijos no tienen una guarda equivalente. Se modifica contenido de un proyecto incompleto antes de su promoción, y una importación posterior del original puede acabar en `Row collision`. |
| **B2-04 — Una dependencia nueva puede cambiar sin invalidar al consumidor** | **Important** | `apps/server/app/snapshots.py:415`; `apps/server/app/migrations/fix1_invariants.py:62` | B ya publicado cambia su colección a C, cuya portada pertenece a A; su membresía durable todavía representa el cierre anterior. El publicador captura la generación y lee el nuevo cierre. Antes del reemplazo, otra transacción modifica esa portada: su identidad aún no figura entre los miembros de B y `entity_song` sólo identifica A. La generación de B no cambia. El publicador instala el documento anterior al cambio y limpia `dirty`, dejando un snapshot obsoleto considerado limpio hasta la auditoría del siguiente arranque. |
| **B2-05 — La parada no cancela la comprobación de copias existentes** | **Important** | `apps/server/app/backup.py:91`; `:178` | `due()` copia cada candidato a memoria mediante `origin.backup(connection)` sin callback de progreso. Si un candidato está retenido por una conexión con bloqueo exclusivo, esa copia puede seguir reintentando mientras `close()` activa `cancel`. El evento sólo se consulta durante la creación de una copia nueva. La parada espera al hilo mediante `shutdown(wait=True)` y queda bloqueada hasta que se libere el candidato. |

**Critical: 0 · Important: 5 · Minor: 0.** Son escenarios deducidos del código, pendientes de reproducción por raíz.

| ID previo | Evaluación independiente | Evidencia |
|---|---|---|
| **R02-01** | **Resuelto** | INSERT/UPDATE de take comprueban raíz canónica; las aristas recalculan descendientes afectados (`fix1_invariants.py:94–114`). |
| **R02-02** | **Resuelto para el defecto previo de linaje** | La validación inversa cubre extremos directos y transitivos (`:116–136`). B2-01 es un defecto distinto de referencias ordinarias transitivas. |
| **R02-03** | **Resuelto para los ejemplos previos** | Separación raíz/dependencias, cierre dirigido y validación de procedencia. Persisten los nuevos defectos B2-02/B2-03. |
| **R02-04** | **Resuelto** | Captura individual de fallos de publicación y auditoría de arranque (`snapshots.py:484–517`). |
| **R02-05** | **Resuelto** | Creación, selección y restauración comparten `validate_database`. B2-05 afecta a cancelación, no a la aceptación de copias inválidas. |
| **R02-06** | **Resuelto** | Eventos registrados desde módulos T02 y uso del logger configurado; `logging.py` suministrado permanece original. |
| **R02-07** | **Reabierto en corrección de invalidación** | La publicación está acotada, pero B2-04 permite limpiar un consumidor obsoleto durante incorporación concurrente de dependencias. El conteo 1/41 no cubre ese intercalado. |
| **R02-08** | **Resuelto** | UPDATE sólo sobre descendientes take afectados y raíces distintas (`fix1_invariants.py:107–114`). |
| **R02-09** | **Resuelto** | Rowid estable y borrados indexables; OLD/NEW de letras se procesan mediante conjuntos de IDs (`:145–184`). |

Esta revisión no acredita QA, aceptación de T02/M-03/M0/M1 ni integración Git.