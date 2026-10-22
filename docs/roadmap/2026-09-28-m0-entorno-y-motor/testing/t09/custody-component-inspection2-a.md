**Lente A — inspección del componente 2: 0 Critical · 0 Important · 0 Minor nuevos. CUST-B01 corregido dentro del alcance declarado.**

Lectura estática de las dos fuentes completas y cotejo del diff íntegro: ambos coinciden con `sources-freeze.json` — producción `9a9bab6f…6260fc`, tests `28c99614…e2eac0`. No ejecuté tests ni probes; las ejecuciones citadas son evidencia registrada.

Rutas abreviadas: `benchmark_custody.py` y `tests/test_benchmark_custody.py` pertenecen a `scripts/eval/`; `tasks.md` pertenece a `docs/roadmap/2026-09-28-m0-entorno-y-motor/`.

| T-09 → criterio del componente | Resultado | Evidencia archivo:línea |
|---|---|---|
| Archivos corresponden al plan | ✓ | `tasks.md:401` declara módulos y pruebas en `scripts/eval/`; `improvement-plan.md:41` remite el detalle al ledger. La custodia implementa la parte individual de O2, `ADR-0046-capsulas-canonicas-y-auditoria-incremental.md:12`. Dos archivos dentro del alcance. |
| Bytes exactos; fuentes pinned y sellos comprobados antes de escribir | ✓ | `benchmark_custody.py:471`, `:482`, `:494`; tests `:59`, `:460`, `:710`. El sello esperado es entrada previamente confiada; no implica autenticación del proveedor. |
| Protección nativa, namespace e identidad del objeto abierto | ✓ | `benchmark_custody.py:253`, `:274`, `:293`, `:415`; tests `:84`, `:122`, `:521`, `:592`. Ruta e identidad de archivo no sustituyen `CompareObjectHandles` para autorizar cierres. |
| **CUST-B01: guard reciclado para el mismo u otro archivo** | ✓ corregido | `benchmark_custody.py:274`, `:285`, `:347`, `:366`; tests `:783`, `:845`. Witness perdido o desprotegido provoca cuarentena, conserva referencias y evita cerrar el handle ajeno. |
| Cierre normal y pérdida/reutilización del principal | ✓ | `benchmark_custody.py:351`; tests `:819`, `:897`. El principal se cierra sólo cuando corresponde al objeto del witness protegido; una reapertura del mismo archivo no acredita ownership. |
| Fallos de setup/cierre; cuarentena persistente y excepción primaria | ✓ | `benchmark_custody.py:366`, `:373`; tests `:933`, `:1022`, `:1062`, `:1090`, `:1110`. Referencias retenidas globalmente; reintentar no anuncia limpieza. |
| Índice cerrado; 64 MiB incluidos encabezado/índice, 128 nombres y lectura ≤256 KiB | ✓ | `benchmark_custody.py:446`, `:555`, `:614`; tests `:401`, `:661`, `:695`. |
| Deadline original, liberación antes de exposición y rechazo tardío | ✓ | `benchmark_custody.py:529`, `:534`, `:624`; tests `:361`, `:612`. No se promete cancelar llamadas síncronas del kernel. |
| Lectura acotada a referencias propias, sin recorrer cápsulas históricas | ✓ | `benchmark_custody.py:602`, `:620`; tests `:188`, `:497`. No acredita continuidad ni aceptación semántica. |
| Tests y evidencia RED/GREEN | ✓ | `custody-inspection-fix1/report.md:5`, `:11`; argv, UTC, exits y JUnit concordantes: RED **1+1+2 fallos**, exit **1**; nuevos **33 PASS**, exit **0**; suite actual **92 PASS / 1 skip**, exit **0**. |
| Cobertura como apoyo | ✓ | `custody-inspection-fix1/native-full-final.stdout.txt:13`: **352/370 sentencias + 106/118 ramas, 93,85 % combinada, cero exclusiones**. El módulo es completamente nuevo en este diff. No consta ejecución de `coverage-gate.py --changed-only`; no la atribuyo. |
| Constitución explícita | ✓ | Sin nueva violación identificada de `docs/CONSTITUTION.md:25` —rutas—, `:33` —ledger/cierre— y `:37` —decisiones documentadas—. Fixture confinada en `test_benchmark_custody.py:33`. |
| Verificación de tareas cerradas | ✓ no hay cierre | `tasks.md:395` mantiene T-09 **en-progreso**, con CA abiertos. La suite del componente no sustituye la Verificación de `tasks.md:403`. No corresponde marcar «verificación declarada sin evidencia». |
| Generados E2 y descripciones E3 | No aplica / ✓ descripción | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar interop. `benchmark_custody.py:3` y `custody-inspection-fix1/report.md:9` describen las limitaciones actuales. |

| T-09 → criterio de aceptación del ledger | Resultado |
|---|---|
| Matriz de configuraciones y duraciones — `tasks.md:407` | ✗ pendiente; componente insuficiente |
| Bind mount frente a copia — `tasks.md:408` | ✗ pendiente |
| Ollama descargado y VRAM de reposo — `tasks.md:409` | ✗ no acreditado por esta entrega |
| Navegador y observación del desbordamiento — `tasks.md:410` | ✗ pendiente |
| Experimento opcional `torch.compile` — `tasks.md:412` | ✗ no acreditado; opcional |
| Recomendación con números — `tasks.md:413` | ✗ pendiente |

**Gaps nuevos: ninguno.** Los CA pendientes no son defectos nuevos de esta entrega parcial.

El alcance excluye código arbitrariamente comprometido que retire y reinstale la protección. `unknown_quarantined` todavía requiere integración que falle cerrada y termine únicamente el worker propio mediante prueba vigente de PID/creation/Job antes de declarar recursos devueltos. Packs, estado canónico, FINAL e integración siguen pendientes; **R09-T13 permanece RED y la siguiente revisión formal sigue siendo 4**, sin reset ni aceptación técnica de T-09.

El skip histórico de privilegios Windows, los 29 directorios históricos y la limitación de caché del launcher UV permanecen explícitos; no permiten afirmar conformidad operacional global. El fallo inicial del injector con pseudo-handle `-1`, corregido a `NULL`, está preservado y no se cuenta como RED del producto.