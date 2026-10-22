**Lente A · inspección3: sin defectos de requisitos en la corrección acotada.**  
**0 Critical · 0 Important · 0 Minor.** Esto no acredita el cierre de T-08.

Revisé el diff completo, las dos fuentes actuales, el brief, el plan, el ledger, la constitución y las evidencias originales. Los SHA-256 actuales coinciden con el freeze: producción `750bd7…`, tests `06836c…`.

| Criterio de revisión | Resultado | Evidencia y escenario |
|---|---|---|
| 1. Implementación declarada | ✓ | [pnpm.py:184](/scripts/pnpm.py:184): prepara el shim completo en un temporal exclusivo y publica mediante `rename` Windows sin reemplazo. Un segundo inicializador valida el ganador antes de devolver éxito. |
| 2. Alcance conforme al plan y `Archivos` | ✓ | Las dos rutas figuran en [tasks.md:286](/docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:286), como prerrequisitos del toolchain de la fase web. El diff contiene únicamente esas rutas; `scope.json` registra dos dentro del alcance, ninguna fuera y ninguna excluida. |
| 3. Tests de la corrección | ✓ | [test_web_tool_entrypoints.py:766](/tests/test_web_tool_entrypoints.py:766): inicializadores simultáneos y escritor parcial. `:848`: ganador válido y destinos ajenos, parciales, hardlink, directorio y junction. `:919`: conservación del temporal sustituido. `:944`: integración posterior con gestor oficial, argv literal y exit37. |
| 3. Cobertura actual | ✓ | `coverage-current.json:1`: **159/165 = 96,36 % del módulo productivo completo**, cero exclusiones. Configuración sin omisiones y una única traza final `.coverage-final-current2`; cobertura de líneas, sin ramas. Contrasté comando, hashes, JSON y base de cobertura abierta en lectura. |
| TDD funcional previo | ✓ | `red-race.xml:1` y `red-partial.xml:1`: fallos funcionales con exit1 a **03:09:20,758693 UTC** y **03:09:25,349425 UTC**, sobre producción anterior `91638a…`. Confirman `FileExistsError` nativo y rechazo de bytes parciales. Los freezes originales coinciden con sus manifiestos. El fallo previo de binding PowerShell no se cuenta como RED. |
| 4. Constitución explícita | ✓ | Confinamiento y revalidación en [pnpm.py:168](/scripts/pnpm.py:168), conforme a [CONSTITUTION.md:25](/docs/CONSTITUTION.md:25). T-08 permanece abierto, conforme a `:33`. No encontré violaciones de principios escritos. |
| 5. Verificación de tareas cerradas | ✓ | Esta entrega no cierra ninguna tarea. T-08 sigue **en-progreso** (`tasks.md:280`); sus verificaciones globales siguen pendientes (`:288`). La ejecución del componente sí consta: `final-current2-after.json`, exit0; `final-current2.xml:1`, **65 PASS, cero errores/fallos/skips**; stdout original concordante. |
| 6. Generados y documentación E2/E3 | No aplica | El diff no toca `commands/`, `agents/` ni `hooks/`. Además, no existe `scripts/export-interop.py` en la raíz. No corresponde ejecutar `--check`; esta corrección tampoco modifica contratos ni el cliente generado. |

Las **27 funciones previas** conservan su AST, incluidos decoradores, parámetros y asserts, frente a la entrega fix1. El fixture añadido captura bytes originales antes de decodificarlos.

**T-08 → criterios de aceptación globales**

Aquí **✗ significa pendiente**, sin constituir un gap de esta entrega parcial.

| Criterio | Estado | Referencia |
|---|---|---|
| Tokens, temas, preferencias y tipografías | ✗ Pendiente | `tasks.md:294` |
| Navegación y reproductor persistente | ✗ Pendiente | `tasks.md:295` |
| Cliente tipado, SSE y conexión directa | ✗ Pendiente | `tasks.md:296` |
| Textos desde `messages/es.json` | ✗ Pendiente | `tasks.md:297` |
| Playwright, stack y smoke E2E | ✗ Pendiente | `tasks.md:298` |
| Dockerfile/Compose, URLs y SSE | ✗ Pendiente | `tasks.md:299` |

La instrumentación de concurrencia utiliza operaciones reales del filesystem Windows; los tests del ganador interponen una creación controlada antes del `rename` real. La integración usa Node/pnpm oficiales y una aplicación sentinel: **no demuestra generación canónica de TypeScript, bootstrap offline completo, UI, build, Docker/Linux ni E2E**.

Comprobaciones propias: lectura, hashes, AST y consultas de cobertura en modo lectura. No reejecuté suites ni hijos nativos, no escribí archivos ni modifiqué el ledger. **QA independiente sigue pendiente; inspección3 conserva su contador.**