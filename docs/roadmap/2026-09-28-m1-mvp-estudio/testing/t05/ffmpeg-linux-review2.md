# FFmpeg Linux — revisión2

A/B/C, tres contextos CLI frescos readonly; C suplementaria por autoridad filesystem. Counter1 y sus hallazgos se conservan. **0 Critical / 0 Important / 0 Minor nuevos.** B01/B02 corregidos; siguiente QA independiente. No aceptación T05/M1 ni Linux nativo.

### Lente A

**Lente A · intento 2: sin gaps nuevos de requisitos o constitución.** Revisión limitada al delta de adquisición FFmpeg: dos archivos, leídos completos y cotejados con el freeze y las copias previas a la ejecución final.

| Tarea → criterio | Resultado | Evidencia `fichero:línea` |
|---|---|---|
| T-05 → CA1: post-proceso Docker, traslado atómico, assets y manifiesto | ✗ Pendiente; correctamente sin marcar. Esta entrega sólo prepara FFmpeg. | `tasks.md:211`; `scripts/fetch_ffmpeg_linux.py:429` |
| T-05 → CA2: `ready`, `song.json` y análisis beats | ✗ Pendiente; correctamente sin marcar. | `tasks.md:212` |
| T-05 → CA3: limpieza del intento aceptado y estado `failed` | ✗ Pendiente; la limpieza del lock de adquisición no acredita este CA. | `tasks.md:213`; `scripts/fetch_ffmpeg_linux.py:332` |
| Alcance y `Archivos` | ✓ Ambos archivos declarados corresponden a preparar el FFmpeg Linux exigido por el plan. Scope capturado: 2 dentro, 0 fuera. | `tasks.md:204`; `improvement-plan.md:59` |
| B-01: fallo/cancelación al escribir `.owner` | ✓ Arranque protegido por `finally`; elimina el lock vacío acreditado y conserva custodia desconocida. Tests comprueban efectos y conservación. | `scripts/fetch_ffmpeg_linux.py:462`; `tests/test_fetch_ffmpeg_linux.py:379`, `:414`, `:456` |
| B-02: ejecutables Linux sin bits X | ✓ `--check` rechaza ambos binarios; tests negativos y positivos diferenciados por plataforma. | `scripts/fetch_ffmpeg_linux.py:383`; `tests/test_fetch_ffmpeg_linux.py:396`, `:492` |
| Tests y cobertura actual individual | ✓ Único módulo productivo cambiado: **334/379 = 88,12665 %**, cero exclusiones, supera 80 %. Copias de producto/tests coinciden por SHA-256 con fuentes actuales. | `final-baseline/coverage.json:1`; `.claude/dev.json:14` |
| TDD de las dos correcciones | ✓ RED funcional previo: lock existente y `--check` retornando 0 incorrectamente; ambos exit 1, dos fallos cada uno. GREEN final: exit 0, **58 PASS**. Argv, UTC y JUnit concordantes. | `red-lock/stdout.txt:1`; `red-mode/stdout.txt:1`; `final-baseline/command.json:1` |
| Principios explícitos | ✓ Sin violaciones nuevas: confinamiento, preparación separada del runtime y tarea abierta. | `docs/CONSTITUTION.md:43`, `:58`, `:79`; `scripts/fetch_ffmpeg_linux.py:71`, `:403` |
| Verificación de tareas cerradas | N/A: T-05 permanece `en-progreso`; las dos verificaciones completas siguen pendientes. No procede «verificación declarada sin evidencia» por cierre. | `tasks.md:198`, `:206` |
| Generados y descripciones E2/E3 | N/A: el delta no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar exportación interop. | `scope.diff:1` |

**Gaps nuevos:** Critical **0**, Important **0**, Minor **0**. Los ✗ anteriores son requisitos abiertos de T-05, no cierres falsos ni defectos nuevos del delta.

Evidencia ejecutada por el implementador, inspeccionada por esta lente: RED/GREEN y `--check` Windows exit 0. El revisor ejecutó únicamente comprobaciones de lectura, hashes y AST; no repitió suites. Modos Linux e identidades alteradas usan **TESTDOUBLE**. Linux nativo, ABI, licencia binaria, Docker, worker y E2E siguen sin acreditar; tampoco hay garantía TOCTOU universal. Se conserva la limitación de copias independientes del helper ausentes por RED.

**Resultado acotado:** conforme para continuar a QA; no acepta T-05 ni M1.

### Lente B

**Sin defectos nuevos de corrección.** Lente B, intento 2: Critical 0 · Important 0 · Minor 0.

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| B01: fallo/cancelación antes de marcar el lock | ✓ Limpia el vacío con identidad acreditada; conserva custodia UNKNOWN | `scripts/fetch_ffmpeg_linux.py:332`, `:464` |
| B02: ejecutables Linux sin bits X | ✓ `--check` rechaza ambos binarios | `scripts/fetch_ffmpeg_linux.py:383` |
| Errores, concurrencia y regresiones del delta | ✓ Sin nuevo escenario concreto de fallo identificado | `scripts/fetch_ffmpeg_linux.py:503`, `tests/test_fetch_ffmpeg_linux.py:379` |

Revisión estática del diff completo y fuentes actuales, con hashes coincidentes con el freeze. Evidencias originales cotejadas: RED funcional, 58 PASS y cobertura del módulo completo **334/379 = 88,12665 %**, cero exclusiones. No ejecuté suites ni probes.

Modos Linux e identidades mutadas son TESTDOUBLE; Linux nativo y garantía TOCTOU universal siguen sin acreditar. Este resultado solo cubre adquisición, sin aceptación de T05/M1.

### Lente C

**Sin hallazgos de seguridad introducidos o reabiertos.** Intento 2: Critical 0 · Important 0 · Minor 0.

Alcance efectivo: `scope.diff`, delta de dos archivos respecto al intento 1; fuentes actuales completas cotejadas con sus SHA-256 congelados. El selector automático dejó C desactivada; root la añadió por las fronteras de limpieza y permisos del sistema de archivos.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin nuevas superficies | `scripts/fetch_ffmpeg_linux.py:332`: el helper añadido utiliza operaciones de archivos, sin intérprete ni comandos. |
| Autenticación y sesión | ✓ Sin cambios | `scripts/fetch_ffmpeg_linux.py:429`: adquisición CLI; el delta no incorpora sesiones ni endpoints. |
| Secretos hardcodeados | ✓ Sin hallazgos | `scripts/fetch_ffmpeg_linux.py:458`: token de custodia generado con UUID, sin credenciales añadidas. |
| Deserialización insegura | ✓ Sin cambios vulnerables | `scripts/fetch_ffmpeg_linux.py:355`: conserva validación del archivo fijado, TAR acotado y procedencia JSON. |
| Path traversal y limpieza | ✓ Sin regresión identificada | `scripts/fetch_ffmpeg_linux.py:332`: exige identidad, contenido vacío o marcador propio único; usa `rmdir`, sin borrado recursivo del lock. |
| SSRF | ✓ Sin nueva superficie | `scripts/fetch_ffmpeg_linux.py:403`: transporte y restricciones de URL permanecen sin cambios. |
| Permisos/autorización | ✓ Comprobación reforzada | `scripts/fetch_ffmpeg_linux.py:383`: exige los tres bits ejecutables para ambos binarios en Linux; conserva rechazo de modos privilegiados. |

Evidencia entregada comprobada por lectura: RED funcional de lock/cancelación y de modos, con argv, UTC, exit 1 y fallos de aserción en JUnit; final exit 0, **58 PASS**, cobertura del módulo completo **334/379 = 88,12665 %**, cero exclusiones. Las fuentes previas a esa ejecución coinciden con las actuales.

Esta revisión ejecutó únicamente lecturas y hashes, sin pruebas de producto ni escrituras. Los modos e identidades alterados son **TESTDOUBLE**; Linux nativo y la garantía universal frente a TOCTOU siguen sin acreditar. Se conserva también la limitación documental del helper por RED. No implica aceptación de T05/M1.