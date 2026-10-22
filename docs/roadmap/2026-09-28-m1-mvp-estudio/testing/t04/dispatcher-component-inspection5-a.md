**Lente A · inspection5: 0 Critical / 0 Important / 0 Minor. Sin defectos de requisitos o constitución identificados en fix4.**

Dictamen limitado a los dos archivos de `scope.diff`. **No acredita T‑04 completa ni aceptación de U1/U2/U3.** Los ✓ siguientes indican conformidad de esta entrega parcial; los ocho criterios generales siguen abiertos.

Referencias: `queue/` = `apps/server/app/queue/`; `tests/` = `apps/server/tests/`; `ledger` = `docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md`.

| T‑04 → criterio de aceptación | Resultado acotado | Evidencia fichero:línea |
|---|---|---|
| CA1 · Carriles, prioridades, FIFO, `not_before` y CPU sin descargar GPU | ✓ Conserva la selección vigente. La desaparición del origen permite continuar al siguiente candidato sin reservar el inválido. | `queue/dispatcher.py:196`; `tests/test_dispatcher_scanning.py:914`, `:940`; `ledger:183` |
| CA2 · `EngineBackend` y adapter `/v1` | ✓ Sin modificación del protocolo ni del adapter. Catalog y envío sintéticos están identificados como tales. | `tests/test_dispatcher_scanning.py:17`, `:895`; `ledger:184` |
| CA3 · Cadena generación → post → beats | ✓ Permanece pendiente; esta entrega no declara implementarla. | `ledger:185`, `:750` |
| CA4 · Resolver por tarea verificada y catálogo cacheado | ✓ Resolver intacto. La normalización ocurre exclusivamente al abrir el origen durante staging. | `queue/inputs.py:213`; `queue/dispatcher.py:170`; `ledger:186` |
| CA5 · Unload y comprobación de VRAM libre | ✓ Conserva preflight, identidad y reserva. Los controles anteriores de ocupación sobrevenida permanecen intactos. | `queue/dispatcher.py:173`, `:189`; `tests/test_dispatcher_scanning.py:705`; `ledger:187` |
| CA6 · NDJSON, cursor y SSE | ✓ Pendiente U2; sin cierre atribuido a fix4. | `ledger:188`, `:750` |
| CA7 · Retry y fallback offload | ✓ Pendiente U2; sin implementación ni aceptación añadidas. | `ledger:189`, `:750` |
| CA8 · Recuperación e identidad durable | ✓ Solo el fallo de apertura del origen se convierte en rechazo preclaim. Conserva las pruebas anteriores de retención posterior al commit; recuperación completa pendiente. | `queue/inputs.py:215`; `queue/admission.py:225`; `tests/test_dispatcher_scanning.py:545`; `ledger:190` |

| Criterio de revisión | Resultado y evidencia |
|---|---|
| 1 · Tareas hechas realmente implementadas | ✓ T‑04 está `en-progreso`, sin ningún CA marcado como cumplido (`ledger:171`, `:183`). La nota de entrega mantiene explícitos los pendientes (`:750`). |
| 2 · Alcance y `Archivos` | ✓ `inputs.py` pertenece a la cola y `test_dispatcher_scanning.py` está declarado expresamente (`ledger:177`); ambos corresponden a Fase 2 (`improvement-plan.md:39`). Diff completo: una modificación de producción y dos pruebas parametrizadas añadidas. Scope registra dos archivos en alcance, ninguno fuera y ninguna exclusión aplicada. |
| 3 · Tests, TDD y cobertura | ✓ Leídas las pruebas añadidas línea a línea (`tests/test_dispatcher_scanning.py:754`, `:862`). Dos RED funcionales antes del cambio, uno automático y otro explícito; siete controles baseline ya verdes, sin contarlos como RED. Cobertura oficial del único módulo de producción cambiado: **116/134 = 86,57 %, cero exclusiones**, reproducida mediante lectura de `coverage-original-data` sobre los bytes actuales. |
| 4 · Constitución explícita | ✓ Sin violación identificada. Conserva cola y VRAM (`docs/CONSTITUTION.md:35`, `:36`), confinamiento (`:43`), cierre mediante verificación (`:58`) y contratos code-first (`:62`). No cambia contratos, infraestructura ni decisiones documentadas. |
| 5 · Verificación ejecutada | ✓ Para esta entrega constan argv, UTC, exit **0**, stdout **215 passed** y JUnit **215 tests / 0 failures / 0 errors**. El ledger registra ese resultado (`:750`) y ambos RED (`:752`, `:754`). **No equivale a la Verificación completa de T‑04** (`:180`); al seguir abierta, no existe cierre sin evidencia. |
| 6 · Generados y documentación E2/E3 | N/A: el diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar `export-interop.py --check`. No introduce cambios contractuales o arquitectónicos que exijan actualizar sus descripciones. |

**Comprobaciones propias, solo lectura:** dos hashes actuales y sus copias finales exactos; 41 fuentes de la corrida, 26 protegidos y siete protegidos por root sin diferencias. Las 19 definiciones anteriores del test conservan su AST y el archivo previo permanece como prefijo idéntico.

**Evidencia de entrega contrastada:** los RED contienen `FileNotFoundError` funcional en JUnit, con producción anterior congelada. El primer GREEN dirigido fue **8 PASS / 1 FAIL** por profundidad incorrecta de la causa; después se comprobó la cadena `PreclaimResolutionError → ResolutionError → FileNotFoundError`, sin cambiar producción. Corrida final: **215 PASS**, sin combinar cobertura histórica.

Filesystem y SQLite son nativos Windows; Catalog, intercalación e inyección de los siete errores son sintéticos explícitos. No ejecuté suites ni sondas funcionales del producto.

**Gaps: ninguno.** Se conserva inspection5 sin reset del historial; QA independiente U1 y revisión integrada siguen pendientes.