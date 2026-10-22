**Lente A — inspección del componente canónico 2: 0 Critical · 0 Important · 0 Minor.** Sin defectos nuevos de requisitos o constitución encontrados en el diff acotado. **T-09 permanece abierta**; este resultado no acredita su implementación completa.

Revisados el diff capturado, las fuentes actuales, los tests, el brief, plan, ledger, constitución y predecesores A/B con adjudicación CANONICAL-TDD01. Las tres fuentes coinciden con el freeze; `benchmark_episode.py` permanece idéntico al predecesor de esta inspección.

| T-09 → criterio del componente | Resultado | Evidencia fichero:línea |
|---|---|---|
| Validador aceptado compartido, conservado como refactor | ✓ | `benchmark_canonical.py:50`. Comprobación propia: cuerpo AST extraído idéntico al wrapper predecesor; `EpisodeProvider` y `EpisodeAcquirer` también idénticos. |
| Transición funcional e historial inmutable | ✓ | `benchmark_canonical.py:403`; `test_benchmark_canonical.py:898,924`. Assertions sobre cursor, aceptaciones, interrupción y exportación sin mutar el estado. |
| Fold independiente desde vacío usando la misma transición | ✓ | `benchmark_canonical.py:477`; tests `:147,959,1075`. Comparación de muestras, hash y ancla externa. |
| Contexto congelado, referencias propias y binding antes de E/S | ✓ | `benchmark_canonical.py:545,581`; tests `:235,984,1016,1178`. Rechazos con cursor intacto; contexto ajeno no alcanza captura nativa. |
| Bytes exactos, inventario cerrado y digest semántico separados | ✓ | `benchmark_canonical.py:289`; tests `:393,737,784`. Corrupción, omisiones, extras y CRLF ejercitados. |
| Plazo original; ninguna aceptación o propuesta tardía expuesta | ✓ | `benchmark_canonical.py:569,609,628,637`; tests `:338,1315,1447`. Comprobaciones posteriores a operación nativa y transición. |
| Commit atómico, candidatos ajenos/obsoletos y concurrencia | ✓ | `benchmark_canonical.py:497,620`; tests `:293,1147,1484`. Dos hilos reales: exactamente una publicación y un rechazo por candidato obsoleto. |
| Rechazo rompe adyacencia y conserva último aceptado | ✓ | `benchmark_canonical.py:421`; test `:427`. Fold, lector anterior y estado incremental coinciden; interrupción impide acreditación. |
| Autoridad revocada o custodia perdida falla cerrado | ✓ | `benchmark_canonical.py:541,642,656`; tests `:547,1198,1232,1395`. Sin publicar cursor ni afirmar recursos devueltos. |
| Frescura externa actual en commit/acreditación | ✓ | `benchmark_canonical.py:630,670`; tests `:665,1356`. Los 901 s son una sonda de política con reloj controlado, declarada como tal. |
| Validación incremental sin releer payload del prefijo | ✓ | `benchmark_canonical.py:601`; test `:147`. Perfil pasante por cápsula nueva. Los pins de acreditación siguen siendo lineales y están declarados. |
| RED funcional anterior a reconstrucción | ✓ | `canonical-tdd-fix1/stages/red01behavior/scripts/eval/benchmark_canonical.py:…`; `commands/red01behavior.json:1` y `commands/red35.json:1`. Scaffold neutral comprobado; reconstrucción posterior en GREEN. |

**CANONICAL-TDD01:** la corrección actual queda sustentada por **34 RED funcionales** con argv, UTC, exit, JUnit y copias previas cuyos hashes coinciden. Ejemplos: cursor `(0,0)` frente a `(1,1)` y dos publicaciones frente a una publicación/un candidato obsoleto. Los antiguos fallos de presencia/API y los incidentes de preparación permanecen separados; no constituyen certificación retrospectiva.

| Criterio transversal | Resultado | Evidencia |
|---|---|---|
| Archivos corresponden al plan | ✓ | `tasks.md:401` incluye módulos y pruebas de `scripts/eval/`; `scope.json` contiene exactamente los dos ficheros modificados, sin rutas fuera de alcance. |
| Tareas marcadas hechas realmente implementadas | N/A | `tasks.md:395`: T-09 sigue **en-progreso**. Este diff no cierra ninguna T-XX. |
| Tests presentes y cobertura actual suficiente | ✓ | Tests leídos línea a línea. `cov/final7-report/coverage.json`: **87,08 % canonical; 81,32 % episode**, módulos completos, líneas+ramas, **cero exclusiones**. |
| Verificación ejecutada para cerrar | N/A | `tasks.md:403`: matriz y lectura del informe pendientes. No ejecuté esa verificación para suplir evidencia. |
| Constitución explícita | ✓ | Sin violaciones identificadas. Confinamiento de fixtures en `test_benchmark_canonical.py:16`; estado conservado abierto conforme a `docs/CONSTITUTION.md:33`. |
| Generados/descripciones E2–E3 | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar `export-interop.py --check`. |

Comprobaciones propias ejecutadas, exclusivamente de lectura: hashes del freeze y **61 fuentes protegidas sin discrepancias**, paridad AST, metadatos/JUnit de los 34 RED, **89 trazas originales y copias idénticas**, y unión SQLite de **1.298 aristas** exactamente igual al combinado oficial. El JUnit final aportado contiene **88 PASS, cero fallos/errores/skips**. No ejecuté pruebas funcionales ni QA nativa independiente. Los sensores son sintéticos; la entrega documenta procesos, Job, PID y creación Windows nativos.

| T-09 → aceptación global | Resultado | Ledger |
|---|---|---|
| Matriz de modelos y duraciones | ✗ Pendiente | `tasks.md:407` |
| Bind mount frente a copia | ✗ Pendiente | `:408` |
| Preflight Ollama/VRAM registrado para la medición | ✗ No acreditado por este componente | `:409` |
| Navegador abierto y observación de spill | ✗ Pendiente | `:410` |
| Experimento opcional `torch.compile` | N/A, opcional | `:412` |
| Recomendación argumentada con números | ✗ Pendiente | `:413` |

Estos pendientes no son nuevos gaps del componente. Runtime/coordinador/rowreader, packs, FINAL completo, T13, matriz160 y QA independiente siguen pendientes. Se conserva la siguiente revisión formal integrada **4**, sin reset.