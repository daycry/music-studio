**Lente B, intento 3/3: ✗ — 1 Important.** Revisión estática del paquete INLINE. No ejecuté herramientas, pruebas ni hashes; las ejecuciones citadas pertenecen a raíz.

| Criterio reevaluado | ✓/✗ | Evidencia y valoración |
|---|:---:|---|
| R02-10: referencias ordinarias tras movimientos transitivos | ✓ | `fix2_invariants.py:106–138` revalida relaciones de los descendientes afectados y referencias inversas. |
| R02-11: versión seleccionada del propio plano | ✓ | `fix2_invariants.py:91–100` cubre selección, movimiento e inserción diferida; `snapshots.py:269–276` comprueba importación. |
| R02-12: soporte protegido hasta promoción validada | ✗ | La actualización directa de `is_dependency_only` permite eludir las guardas; escenario abajo. |
| R02-13: publicación concurrente y dependencia nueva | ✓ | `snapshots.py:414–424` captura reloj, generación y cierre en una lectura SQLite; `:453–486` adquiere escritura antes del CAS y conserva dirty ante diferencias. |
| R02-14: cancelación durante copia de candidatos bloqueados | ✓ | `backup.py:93–103` incorpora timeout cero y callback; `InterruptedError` sale del filtro de candidatos y llega a `run`. |
| R02-15: consultas individuales del cierre | ✓ | `closure_rows.py:30–79` agrupa consultas en lotes de 400 y reutiliza filas recuperadas. |
| R02-16: escaneos repetidos de relaciones y sección primaria | ✓ | `closure_rows.py:82–106` indexa relaciones; `snapshots.py:305–350` reutiliza pertenencias y un conjunto de identidades primarias. Esto corrige los recorridos denunciados, sin afirmar coste lineal de todos los algoritmos. |
| R02-17: recorrer necesariamente toda la retención y duplicar initial | ✓ | `backup.py:83–108` termina en el candidato válido más reciente; `:154–156` aplaza el siguiente chequeo. |

| Gap | Grado | Fichero:línea | Escenario concreto |
|---|---|---|---|
| R02-12 — promoción ordinaria elude protección | **Important** | `apps/server/app/migrations/fix2_invariants.py:84–86`; `apps/server/app/migrations/fix1_invariants.py:32` | Tras importar B con A como soporte, ejecutar `UPDATE song SET is_dependency_only=0 WHERE id=A` fuera de `restore` tiene éxito: la nueva guarda omite todo UPDATE de song y la anterior exige que **OLD y NEW** sean soporte. No se exige presencia en `snapshot_import` ni importación completa compatible. A queda promovida con contenido parcial, entra en FTS y sus jobs pasan a `dispatchable_job`; después se permite editar sus hijos. También puede combinarse la promoción con `title=...` en el mismo UPDATE. Las pruebas aportadas verifican edición de hijos y promoción mediante restore, pero no esta transición directa. |

**Critical: 0 · Important: 1 · Minor: 0.**

R02-07 muestra corregidas sus partes concurrente y de acceso al cierre examinadas aquí; la valoración final de rendimiento corresponde a D. Los demás IDs previamente aprobados permanecen sin reabrir. La adjudicación y el cierre de IDs corresponden a raíz; este resultado no acredita QA, cierre de T02, M-03, Git ni aceptación humana.