**Lente A — inspección de componente 4: sin defectos de requisitos o constitución en la dependencia `canonical-lease-unit1`.** Critical: **0** · Important: **0** · Minor: **0**. No constituye aceptación integrada de T-09.

| T-09 → criterio de la dependencia | Resultado | Evidencia `fichero:línea` |
|---|---|---|
| Checkout O(1), snapshot e historia inmutables, máximo una lease activa | ✓ | `benchmark_canonical.py:698`; `test_benchmark_canonical.py:1769,2188` |
| Autoridad exacta por instancia, capability e hilo; copias, JSON y forjados rechazados | ✓ | `benchmark_canonical.py:717`; `test_benchmark_canonical.py:1825` |
| Witness fuera del lock de estado, sin payload histórico | ✓ | `benchmark_canonical.py:737`; `test_benchmark_canonical.py:1656,1769` |
| Presupuesto absoluto de `accredit`, fijado antes de esperar y sin renovación por witness | ✓ | `benchmark_canonical.py:802`; `test_benchmark_canonical.py:1732,1915` |
| Head sano posterior conserva cursor/prefix seleccionados | ✓ | `benchmark_canonical.py:762`; `test_benchmark_canonical.py:1769` |
| Rechazo, interrupción, cuarentena y epoch invalidan antes del retorno | ✓ | `benchmark_canonical.py:578,676,754,779`; `test_benchmark_canonical.py:2022,2065,2145` |
| Frescura actual del snapshot, incluso sin datos nuevos; frontera 900/901 | ✓ | `benchmark_canonical.py:771`; `test_benchmark_canonical.py:1986` |
| Pérdida nativa de pin conserva causa y referencias; falla cerrado | ✓ | `benchmark_canonical.py:682`; `test_benchmark_canonical.py:1879,2125` |
| Release idempotente; liberación extranjera no borra al propietario | ✓ | `benchmark_canonical.py:790`; `test_benchmark_canonical.py:1825,2188` |
| Semántica previa y pruebas existentes preservadas | ✓ | Comparación AST: 44 funciones previas del test intactas; `transition` y `validate_accepted` intactos. Los 65 protegidos coinciden por SHA-256/tamaño |
| Alcance declarado corresponde al plan | ✓ | `tasks.md:401,2237,2242`: únicamente estado canónico y test existente; diff completo de dos ficheros |
| Constitución explícita respetada | ✓ | `docs/CONSTITUTION.md:25,32,33,35`: confinamiento, idioma, ledger y contratos conservados |
| Generados/descripciones E2/E3 | N/A | No se modifican `commands/`, `agents/` ni `hooks/`; no procede ejecutar exportador interop |

La evidencia entregada y cotejada registra **127 PASS = 102 canónicos + 25 vecinos**, sin fallos, errores ni skips, exit **0**. La cobertura oficial fresca del módulo completo es **90,349417 %**: 417/447 líneas y 126/154 ramas, **cero exclusiones**, sin promedio ni unión histórica. Archivo: `runs/final-frozen/.coverage`; salida: `runs/final-frozen/stdout.txt:3`. Los bytes ejecutados coinciden con las fuentes actuales congeladas.

Los tres RED originales tienen argv, UTC, JUnit y fuente predecesora exacta: bloqueo de ingreso, bloqueo de revocación y presupuesto acumulado. Son fallos funcionales. Los Event controlan scheduling y el reloj inyectado comprueba política; los witnesses, archivos y procesos son nativos. Cotejados **129 pares nacimiento/cierre** por UUID/PID/FILETIME/Job, con Job vacío y reader unido. Esto no acredita interrupción del store ni cadencia real.

| T-09 → criterio de aceptación global | Resultado |
|---|---|
| Matriz completa de configuraciones y duraciones | ✗ Pendiente |
| Comparación bind mount/copia | ✗ Pendiente |
| Preflight Ollama/VRAM para matriz completa | ✗ Pendiente |
| Navegador abierto y observación del desbordamiento | ✗ Pendiente |
| `torch.compile` | N/A: opcional |
| Recomendación sustentada por matriz completa | ✗ Pendiente |

**Verificación de cierre:** T-09 continúa `en-progreso` (`tasks.md:395`); esta dependencia no declara ejecutada la Verificación global ni cerrada la tarea. Por tanto, no hay gap «verificación declarada sin evidencia».

Comprobaciones propias: lectura del diff y fuentes, AST, hashes, recibos, JUnit y SQLite de cobertura en modo lectura. **No repetí tests, no escribí archivos ni modifiqué el ledger.** Sigue adjudicación del orquestador y QA independiente; inspección de componente 4 y revisión formal integrada 4 permanecen distintas.