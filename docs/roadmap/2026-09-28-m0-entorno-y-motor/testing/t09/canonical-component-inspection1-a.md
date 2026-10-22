**Lente A: 0 Critical · 1 Important · 0 Minor.** La implementación acotada es coherente con el alcance; falta acreditar TDD funcional por capacidad. No procede certificar la entrega como limpia.

Revisados el diff completo, las tres fuentes actuales, los tests, el brief, plan, ledger, constitución y evidencias originales. Los SHA-256 actuales coinciden con el freeze. No ejecuté suites ni modificqué archivos.

| T-09 → criterio del componente | Resultado | Evidencia fichero:línea |
|---|---|---|
| Semántica aceptada compartida con el wrapper offline | ✓ | `benchmark_canonical.py:52`; `benchmark_episode.py:781`. El cuerpo anterior se sustituye por la llamada compartida. |
| Fold independiente desde estado vacío | ✓ | `benchmark_canonical.py:388`; `test_benchmark_canonical.py:88,368`: comparación con originales, muestras y hash. |
| Contexto congelado, ancla externa y referencias emitidas por la instancia | ✓ | `benchmark_canonical.py:488,533,587`; tests `:176,234`. |
| Bytes exactos y sellos semánticos separados; JSON y lecturas acotados | ✓ | `benchmark_canonical.py:422`; tests `:334,678,725`: corrupción, omisiones, extras y CRLF. |
| Deadline original y commit atómico; rechazo de candidates obsoletos | ✓ | `benchmark_canonical.py:628`; tests `:234,279,565`. |
| Rechazo rompe adyacencia y conserva último aceptado; interrupción sin acreditación | ✓ | `benchmark_canonical.py:366`; tests `:368,454,780,805`. |
| Pérdida de autoridad falla cerrado, sin afirmar recursos devueltos | ✓ | `benchmark_canonical.py:523,654`; tests `:488,528`. |
| Transición sin copiar ni revalidar payload del prefijo | ✓ | `benchmark_canonical.py:321`; test `:88`, perfiles pass-through. |
| Frescura actual en cada acreditación | ✓ | `benchmark_canonical.py:672`; test `:606`. Los 901 s se prueban offline con reloj explícito, correctamente declarados. |
| Tests presentes y cobertura completa actual ≥80 %, sin exclusiones | ✓ | `cov/frozen3/coverage.json`: **84,0336 % canonical; 81,7410 % episode**, líneas+ramas. JUnit: **63 tests, 0 fallos/errores/skips**. |
| RED funcional anterior al código por capacidad | ✗ | Gap A-01 siguiente. |

**Gap A-01 — Important: evidencia TDD insuficiente por comportamiento.**

El [brief:134](../../../../../.cache/dev-cycle/t09/canonical-component-inspection1/task-brief.txt:134) exige fallar por la razón correcta antes de implementar. Sin embargo, **19 fallos iniciales** terminan en la comprobación de disponibilidad de [test_benchmark_canonical.py:45](../../../../../scripts/eval/tests/test_benchmark_canonical.py:45), antes de ejercitar equivalencia, binding, rollback, deadlines o manipulación de originales. Ejemplo: [RED de equivalencia:7](../../../../../.cache/dev-cycle/t09/canonical-state-unit/commands/red-test_native_incremental_equals_independent_original_fold.stdout:7).

Otros tres fallos acreditan ausencia de atributos/API (`disposition`, `lose_authority`, `last_accepted_receipt`). Los RED funcionales encontrados son progreso monotónico y ownership —tres casos—. Las ejecuciones inicialmente verdes de rechazo e interrupción son regresiones suplementarias.

**Escenario concreto:** una implementación que sólo haga disponible el módulo supera aquellos 19 puntos de fallo sin demostrar todavía ninguna de esas conductas. Los GREEN posteriores verifican funcionamiento actual, pero no acreditan retrospectivamente el RED funcional exigido. Los «25 fallos RED» de [report.md:15](../../../../../.cache/dev-cycle/t09/canonical-state-unit/report.md:15) no permiten certificar TDD por capacidad.

| Criterio transversal | Resultado | Evidencia |
|---|---|---|
| Archivos corresponden al plan | ✓ | `tasks.md:401` incluye módulos y pruebas de `scripts/eval/`; las tres rutas respetan el ownership acotado. |
| Tareas hechas realmente cerradas | ✓ | `tasks.md:395`: T-09 sigue **en-progreso**; esta entrega no cierra ninguna T-XX. |
| Verificación declarada ejecutada para cerrar | N/A | `tasks.md:403`: la matriz no queda acreditada por este componente. No hay cierre sin evidencia que imputar. |
| Constitución explícita | ✓ | Sin violaciones identificadas en este diff; confinamiento en `benchmark_episode.py:51`, sin cambios de contratos, pesos, BD o despliegue. |
| Generados/descriptores E2–E3 | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador interop. |

| T-09 → aceptación global del ledger | Resultado |
|---|---|
| Matriz de modelos y duraciones — `tasks.md:407` | ✗ Pendiente |
| Bind mount frente a copia — `:408` | ✗ Pendiente |
| Preflight Ollama/VRAM registrado para medición — `:409` | ✗ No acreditado por esta entrega |
| Navegador y observación de spill — `:410` | ✗ Pendiente |
| Experimento opcional `torch.compile` — `:412` | N/A, opcional |
| Recomendación con números — `:413` | ✗ Pendiente |

Estos pendientes globales no son nuevos gaps del componente. Integración runtime/coordinador/row-reader, packs y FINAL completo permanecen fuera de esta entrega. Los pins de acreditación siguen teniendo coste lineal, declarado en `report.md:45`; no hay evidencia nueva para elevar esa limitación a gap de rendimiento. Se conserva la revisión formal siguiente **4** y los RED previos de T13.

La cobertura y los PASS citados son evidencia de la entrega inspeccionada. Mis comprobaciones ejecutadas fueron hashes, lectura de JSON/JUnit y paridad AST de los clones; no QA nativa independiente.