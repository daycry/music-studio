**Lente A: sin defectos nuevos en el componente de custodia individual y la fixture corregida.** Critical: **0** · Important: **0** · Minor: **0**. Dictamen limitado a los dos archivos del freeze; no constituye aceptación de T-09 ni revisión formal integrada intento 4.

Leí todo `scope.diff` y ambas fuentes actuales. Sus SHA-256 coinciden con `sources-freeze.json`: producción `97834668…a622d8`; tests `e04b52c0…af039`.

| T-09 → criterio del componente | Resultado | Evidencia fichero:línea |
|---|---|---|
| Archivos acordes con el plan | ✓ | `tasks.md:401` admite módulos y pruebas en `scripts/eval/`; los dos archivos implementan la custodia individual elegida en `ADR-0046:12`. Scope: 2 dentro, 0 fuera, 0 avisos. |
| Bytes exactos y sellos comprobados antes de grabar | ✓ | `benchmark_custody.py:409`; tests de CRLF/NUL y original posteriormente modificado en `test_benchmark_custody.py:59`, y ausencia de grabación con sello incorrecto en `:460`. |
| Protección nativa e identidad del objeto | ✓ | `benchmark_custody.py:230`, `:255`, `:275`; denegaciones reales en tests `:84`, escritor previo `:122`, junction `:521`, hardlink preexistente `:592`. |
| Pérdida de pin revoca lectura; cierre preserva handles ajenos | ✓ | `benchmark_custody.py:306`, `:547`, `:555`; tests `:216`, `:298`, `:332`, incluida reutilización del slot para el mismo archivo. |
| Índice cerrado y límites reales | ✓ | `benchmark_custody.py:366`, `:483`, `:540`; corrupción parametrizada en tests `:401`, cápsula exactamente 64 MiB en `:661`, 128 entradas vacías en `:695`. |
| Deadline único, sin exposición tardía | ✓ | `benchmark_custody.py:185`, `:450`, `:456`, `:552`; tests `:361` y `:612`. Las llamadas síncronas no se cancelan; el retorno tardío se rechaza. |
| Referencias propias; lectura sin recorrer historial | ✓ | `benchmark_custody.py:530`; tests de store ajeno `:188`, identificadores inválidos `:482` y observación de lecturas `:497`. No acredita autenticación del proveedor. |
| Durabilidad de bytes y limpieza propia | ✓ | `benchmark_custody.py:448` hace flush/fsync antes de verificar; `:476` retira únicamente el intento propio no publicado; `:555` conserva cápsulas al cerrar y revoca acceso. No acredita recuperación semántica tras reinicio. |
| Fixture confinada y preservación de fase anterior | ✓ | `test_benchmark_custody.py:33` resuelve y confina la raíz a `.cache`, crea UUID propio y limpia ese UUID. `custody-fixture-fix/report.md:5` documenta AST preservado; `:9` preservación y cleanup. |
| Tests y cobertura del código nuevo | ✓ | `custody-fixture-fix/native-unit.stdout.txt:1`: **59 passed, 1 skipped**, exit **0**. Cobertura oficial del módulo nuevo completo: **315/334 sentencias, 93/104 ramas, combinada 93,15 %, 0 exclusiones**. Leí los tests; el porcentaje es apoyo, no sustituto. No atribuyo ejecución de `coverage-gate.py --changed-only`. |
| Constitución explícita | ✓ | Sin nueva violación identificada de `docs/CONSTITUTION.md:43` — rutas dentro del proyecto—, `:58` —estado y cierre— ni `:66` —decisiones documentadas—. |
| Verificación de tareas cerradas | ✓ / no aplica cierre | `tasks.md:395` mantiene T-09 **en-progreso** y todos sus CA abiertos. No hay cierre en este diff que requiera evidencia de la matriz completa. La suite del componente no sustituye `tasks.md:403`. |
| Generados E2 y descripciones E3 | No aplica | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador interop. La descripción del módulo limita expresamente su alcance en `benchmark_custody.py:3`. |

| T-09 → criterio de aceptación del ledger | Resultado actual |
|---|---|
| Matriz de configuraciones y duraciones — `tasks.md:408` | ✗ pendiente; este componente no la acredita |
| Bind mount frente a copia — `tasks.md:409` | ✗ pendiente |
| Ollama descargado y VRAM de reposo — `tasks.md:410` | ✗ pendiente para la medición |
| Navegador, observación y desbordamiento — `tasks.md:411` | ✗ pendiente |
| Experimento opcional `torch.compile` — `tasks.md:413` | ✗ no acreditado; opcional |
| Recomendación con números — `tasks.md:414` | ✗ pendiente |

Estos pendientes **no son gaps nuevos de esta entrega parcial**. Se conserva revisión 3 y R09-T08…T13; no reabro el rebate R09-T10 ni doy T13 por resuelto.

**Evidencia propia:** inspección estática y cotejo SHA-256 de los **213 archivos** del inventario post-terminal, sin discrepancias. No ejecuté tests ni probes, ni escribí archivos. Las ejecuciones nativas citadas son evidencia histórica custodiada. El skip de symlink no acredita ese caso; la junction real sí figura aprobada. Linux sólo tiene rechazo fail-closed probado mediante inyección de plataforma.

El incidente histórico de **29 directorios vacíos** fuera de la fase propia permanece explícito en `custody-foundation-unit/attempt-20261007-native/cleanup.json`; impide afirmar conformidad operacional plena, aunque sigue dentro del repositorio y no constituye una nueva violación constitucional del diff corregido.