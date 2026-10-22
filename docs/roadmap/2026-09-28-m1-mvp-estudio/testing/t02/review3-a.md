**Lente A — intento 3/3: ✗. R02-12 conserva un gap Important: la promoción puede realizarse mediante SQL ordinario sin importación validada.**

Revisión estática del paquete INLINE. No ejecuté herramientas, pruebas ni hashes. Las ejecuciones, porcentajes y comprobaciones de custodia citados pertenecen a raíz.

| T-02 → criterio | ✓/✗ | Evidencia y evaluación |
|---|:---:|---|
| 23 tablas, campos comunes y usuario `local` | ✓ | Baseline conservado; `test_schema_t02.py:35` comprueba tablas, columnas y usuario inicial. |
| WAL y claves foráneas por conexión | ✓ | `db.py:43–52`; comprobación de dos conexiones en `test_schema_t02.py:70`. |
| FTS transaccional sobre canción activa y letra vigente | ✓ | `fix1_invariants.py:140`; tests de selección, actualización, papelera, rollback y reconstrucción. Fix2 conserva estos mecanismos. |
| Raíz canónica, varios padres y papelera sin perder hijos | ✓ | Guardas y recomputación de Fix1 conservadas; tests de linaje y borrado lógico suministrados. |
| Pertenencia ordinaria transitiva — R02-10 | ✓ | `fix2_invariants.py:106–138` revalida relaciones de descendientes afectados y referencias inversas. Regresión SQL/Core/ORM en `test_review_fix2_t02.py:33`. |
| Selección de versión del propio plano — R02-11 | ✓ | Guardas directas, inversas y de inserción diferida en `fix2_invariants.py:91–100`; validación JSON en `snapshots.py:269`. Tests de selección y ciclos diferidos leídos. |
| Raíz completa y dependencias dirigidas, con IDs e historia conservados | ✓ | `snapshots.py:72–117`, clasificación y procedencia en `:385–408`; no se expanden todos los hijos de canciones de soporte. |
| Soporte no editable hasta promoción validada — R02-12 | ✗ | Las guardas de hijos cubren los escenarios aportados, pero la actualización ordinaria de `is_dependency_only` permite eludirlas. Escenario detallado abajo. |
| Publicación consistente y reparación concurrente — R02-13 | ✓ | `snapshots.py:414–424` captura revisión, generación y cierre en una misma transacción de lectura; `:453–486` adquiere escritura antes del CAS. Un cambio concurrente conserva `dirty`. Tests de dependencia nueva, WAL y publicador competidor leídos. |
| Publicación acotada — parte de R02-07 relevante para A | ✓ | Selección de pendientes en `snapshots.py:519`; acceso por lotes y caché en `closure_rows.py`. La revisión global conservadora afecta a la raíz publicada, sin ordenar regenerar toda la biblioteca. |
| Importación transaccional, conflictos y medios existentes | ✓ | `snapshots.py:537–615` valida, comprueba hashes y colisiones, abre la excepción de importación y la elimina dentro de la transacción. |
| Backup nativo, restauración WAL/FTS y rotación propia | ✓ | `backup.py:23–76`, `:116–141`; pruebas de restauración y conservación de copia previa suministradas. |
| Cancelación de candidatos — R02-14 | ✓ | `backup.py:93–103` incorpora `timeout=0`, páginas limitadas y callback; `InterruptedError` no queda atrapado como candidato inválido. Regresión con bloqueo exclusivo en `test_review_fix2_t02.py:264`. |
| Comprobar el último backup válido — R02-17 | ✓ | Orden descendente y parada al primer válido en `backup.py:83–108`; espera inicial en `:154–156`. Tests de fallback y ausencia de duplicación inmediata leídos. |
| Tests y cobertura | ✓ | Raíz aporta **305 pass / 3 skip**, con tres suplementos Linux separados; los 43 casos nuevos ya están incluidos. **631/667 = 94,6027 % corresponde a cinco módulos completos, no al diff**, mínimo 91,957 %, sin exclusiones. Apoya la revisión; no cubre el bypass señalado. |
| Alcance frente al plan | ✓ | Persistencia, helpers, migraciones, contratos, lifespan y tests corresponden a T-02. Scope aportado: 29 archivos, sin elementos fuera de alcance. |
| Constitución explícita | ✓ | No identifico una infracción constitucional adicional introducida por Fix2. La migración `0003` es aditiva, conforme a `CONSTITUTION.md:39`. El gap es de ADR-0044 y del criterio de soporte. |
| Verificación ejecutada y estado honesto | ✓ | Evidencia de raíz: selección exacta **30 pass / 278 deselected**, ciclos vacíos/poblados y diez operaciones CLI exit 0. `tasks.md:101` mantiene `en-revision` y criterios abiertos; no declara cierre ni aceptación M-03. |
| Generado y descrito actualizado | ✓ | Paridad de contratos y wheel atribuida a raíz. `datos.md:350` y `database-design.md:30` describen la candidata `0003` y mantienen revisión/QA pendientes. |

Interop **no aplica**: el diff no toca `commands/`, `agents/` ni `hooks/`. El criterio condicional OpenAPI **no aplica**: los contratos modificados son JSON Schema.

| ID | Grado | Fichero:línea | Escenario concreto |
|---|---|---|---|
| **R02-12 — corrección incompleta** | **Important** | `apps/server/app/migrations/fix2_invariants.py:84`; `apps/server/app/migrations/fix1_invariants.py:32` | Después de importar B con A como soporte, ejecutar `UPDATE song SET is_dependency_only=0 WHERE id=A` mediante SQL/Core/ORM ordinario. Fix2 omite expresamente la guarda UPDATE de `song`; la guarda anterior sólo rechaza cuando **OLD y NEW siguen siendo soporte**. Por tanto, la operación promueve A sin importar su proyecto completo. Una actualización posterior de `take.rating`, `lyrics_version.text` o `artwork.prompt` ya pasa las guardas de hijos porque A dejó de estar marcada como soporte. Además, FTS puede incorporar ese proyecto incompleto. Incumple `ADR-0044:18`, que exige promoción mediante importación validada del proyecto completo con filas compatibles. Los tests aportados verifican promoción por `restore`, pero no este cambio ordinario de la marca. |

**Critical: 0 · Important: 1 · Minor: 0.**

R02-11 y R02-13 muestran corrección suficiente desde A. R02-12 permanece abierto por el escenario anterior; los demás IDs conservan su historial. La adjudicación fusionada y el cierre corresponden a raíz. Este resultado no acredita QA, cierre de T-02, M-03, Git ni aceptación humana.