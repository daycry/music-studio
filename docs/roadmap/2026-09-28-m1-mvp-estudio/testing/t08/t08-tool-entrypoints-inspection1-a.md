**Lente A · T08 / inspection1: 0 Critical · 0 Important · 0 Minor.** Conforme para la unidad acotada de entrypoints e instalación. **No acredita el cierre de T-08.**

| Criterio de revisión | Resultado | Evidencia |
|---|---|---|
| 1. Tareas declaradas hechas | ✓ | T-08 permanece `en-progreso`, con sus seis CA abiertos: `tasks.md:280,294–299`. Esta entrega no declara completada la tarea. |
| 2. Alcance del plan y `Archivos` | ✓ | Los diez archivos corresponden al prerrequisito autorizado en `tasks.md:786`; los ocho entrypoints/tests aparecen en `tasks.md:286`. `scope-current.json`: diez dentro, ninguno fuera. |
| 3. Tests y cobertura | ✓ | Lectura de assertions en `tests/test_web_tool_entrypoints.py:77,98,115,178,197,216,259,268,277,294,301,332,354,378`. JUnit final: **43 PASS**, exit 0. Cobertura oficial del módulo completo `scripts/pnpm.py`: **88/91 = 96,70 %**, cero exclusiones; comprobado también el dato original `.coverage-final`, sin unión ni promedio histórico. |
| 4. Constitución explícita | ✓ | Confinamiento y entorno propio en `scripts/pnpm.py:138–175`; ejecución Python aislada en `scripts/pnpm.ps1:12`. Sin violación identificada de `docs/CONSTITUTION.md:43,58,66`. |
| 5. Verificación de tareas cerradas | ✓ / no aplica al cierre | T-08 no está cerrada. Las verificaciones globales de `tasks.md:289–291` siguen pendientes; no se sustituyen por los tests de esta unidad. |
| 6. Generados y documentación E2/E3 | No aplica | El diff acotado no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar `export-interop.py --check`. |

| T-08 → criterio de aceptación | Resultado | Localización |
|---|---|---|
| Tokens, temas, preferencias y fuentes | ✗ Pendiente; pins de fuentes incorporados, sin UI | `tasks.md:294`; `apps/web/package.json:34–36` |
| Navegación y reproductor persistente | ✗ Pendiente | `tasks.md:295` |
| Cliente tipado, SSE y conexión directa | ✗ CA completo pendiente | `tasks.md:296` |
| Texto desde `messages/es.json` | ✗ Pendiente | `tasks.md:297` |
| Infraestructura E2E y smoke | ✗ Pendiente | `tasks.md:298` |
| Docker web/server/mock y validación de URLs/SSE | ✗ Pendiente | `tasks.md:299` |

Estos pendientes están declarados y quedan fuera de la unidad revisada; **no son gaps de esta entrega**.

Comprobación propia en solo lectura: diez fuentes congeladas exactas, 2.935 archivos de herramientas exactos y 27.919 archivos instalados inventariados exactos. Los 23 pins coinciden con el candidato autorizado y el lock es byteidéntico. Instalados **482** artefactos; **127** ausentes por layout/opcionalidad. Se distinguen **27.667 payloads TAR** de **252 shims generados**.

Evidencia cualificada: PowerShell y Bash tienen recibos nativos; transporte y bootstrap incluyen fronteras explícitamente simuladas. Parser 112 PASS y typecheck canónico exit 0 son recibos de la revisión anterior del wrapper, con manifiestos actuales iguales. Los dos typechecks profundos interrumpidos no cuentan como verde. El exit real del actor continúa desconocido; el lanzador exterior terminó con 1 por la colisión de metadatos, sin invalidar ni convertir en éxito los recibos individuales.

**Gaps de requisitos/constitución: ninguno.** No ejecuté wrappers, instalaciones ni suites GREEN; no escribí archivos.