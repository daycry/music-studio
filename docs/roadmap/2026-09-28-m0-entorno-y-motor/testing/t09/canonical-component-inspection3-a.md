**Lente A, inspección canónica 3: 0 Critical · 0 Important · 0 Minor.** Sin defectos nuevos de requisitos o constitución en el diff acotado. **T-09 sigue abierta**; este resultado no acredita la tarea completa.

Revisados el diff completo, las fuentes actuales, los tests, el brief, el plan, el ledger y las inspecciones anteriores con su adjudicación.

| T-09 → criterio del componente | Resultado | Evidencia fichero:línea |
|---|---|---|
| B01: congelar intentos y anclas antes de comparación/E/S | ✓ | `scripts/eval/benchmark_canonical.py:485`; `scripts/eval/tests/test_benchmark_canonical.py:101`. Copias separadas; intercalación al leer `request.json` ejercita intento, ancla, ambos y transición directa. |
| Transición conserva identidad y evita alias de entradas/exportaciones | ✓ | `benchmark_canonical.py:416`; `test_benchmark_canonical.py:150,172`. Comprueba recibo, historial, muestras y estados rejected/interrupted. |
| Mantener coste incremental O(delta), sin copiar prefijo | ✓ | `benchmark_canonical.py:416,478`; `test_benchmark_canonical.py:198,256,933`. Solo se copian attempt/context/record; historial enlazado conservado. |
| Preservar validador, funciones y pruebas anteriores | ✓ | `benchmark_canonical.py:51`; `compatibility-final.json:1`. Comprobación AST propia: únicamente cambian `transition` y `fold_originals`; funciones/tests anteriores idénticos. |
| RED funcional anterior al cambio | ✓ | `runs/red-attempt/receipt.json:1`, `runs/baseline-both/receipt.json:1`, `runs/baseline-transition/receipt.json:1`. Tres exit1/JUnit con PID publicado 0 frente al PID original; fuentes anteriores archivadas. Ancla sola fue control verde. |

| Criterio transversal | Resultado | Evidencia |
|---|---|---|
| Tareas hechas realmente implementadas | N/A | `tasks.md:398`: T-09 en-progreso; el diff no cierra ninguna tarea. |
| Archivos corresponden al alcance aprobado | ✓ | `improvement-plan.md:38,40`; `tasks.md:401`. Los dos cambios pertenecen a módulos/pruebas de `scripts/eval/`; `scope.json:5` confirma ambos. |
| Tests presentes y cobertura suficiente | ✓ | Tests leídos línea a línea. `coverage.json:1`: **87,24 %** del único módulo productivo cambiado, completo, líneas+ramas, **cero exclusiones**. Base `.coverage` contrastada con las fuentes actuales y el parser de Coverage. |
| Verificación declarada de tareas cerradas | N/A | `tasks.md:403`: matriz y lectura del informe siguen pendientes. No las ejecuté para suplir evidencia. |
| Constitución explícita | ✓ | Sin violaciones identificadas. Fixtures confinadas (`test_benchmark_canonical.py:16`) conforme a `docs/CONSTITUTION.md:25`; tarea abierta conforme a `:33`. |
| Generados/descripciones E2–E3 | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador interop. |

| T-09 → aceptación global | Resultado | Evidencia |
|---|---|---|
| Matriz de configuraciones y duraciones | ✗ Pendiente | `tasks.md:407` |
| Bind mount frente a copia | ✗ Pendiente | `tasks.md:408` |
| Preflight Ollama/VRAM para la medición | ✗ No acreditado por este componente | `tasks.md:409` |
| Navegador abierto y observación de spill | ✗ Pendiente | `tasks.md:410` |
| Experimento `torch.compile` | N/A, opcional | `tasks.md:412` |
| Recomendación argumentada con números | ✗ Pendiente | `tasks.md:413` |

**Evidencia aportada cotejada:** 94 PASS, cero fallos/errores/skips; 94 pares originales nacimiento/cleanup con identidad coincidente, Job vacío y reader terminado. **Comprobaciones propias de lectura:** hashes actuales/freeze, 62 protegidos exactos, AST, recibos/JUnit y cobertura. No ejecuté la suite ni QA nativa.

Procesos y relojes Windows reales; sensores sintéticos e intercalación inyectada. Los bytes del helper global en RED temprano siguen **UNKNOWN**, expresamente documentados. Runtime/coordinador/rowreader, packs/FINAL, T13 y QA independiente permanecen pendientes; revisión formal integrada **4**, sin reset.