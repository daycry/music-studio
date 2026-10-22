**Lente A — inspección2: sin defectos de requisitos en la corrección acotada.** Gaps: **0 Critical · 0 Important · 0 Minor**. No supone aceptación global de T-08.

Revisados el diff completo de dos archivos, las fuentes actuales, el brief, el plan, el ledger y las evidencias congeladas. Los SHA-256 actuales coinciden con la entrega.

| Criterio de revisión | Resultado | Evidencia |
|---|---|---|
| Implementación del componente declarado | ✓ | El shim propio permite el pnpm anidado y vuelve a validar herramientas/configuración: `scripts/pnpm.py:207`, `scripts/pnpm.py:230`. Test funcional: `tests/test_web_tool_entrypoints.py:511`. |
| Alcance conforme al plan y `Archivos` | ✓ | Ambas rutas están declaradas en `tasks.md:286` y sirven al prerrequisito del toolchain de la fase web (`improvement-plan.md:41`). `scope.json`: dos archivos dentro del alcance, ninguno fuera. |
| Tests de la corrección | ✓ | Lectura de tests: ejecución nativa (`:511`), argv/exit37 (`:522`), destinos ajenos (`:535`), revalidación anidada (`:570`), shim alterado (`:595`) y runtime estable (`:605`). |
| Cobertura actual | ✓ | `coverage-current.json:1`: **113/116 = 97,41379 % del módulo completo**, cero exclusiones. Una traza `.coverage-final-current`, sobre los hashes actuales; supera el 80 % sin promediar otros módulos. |
| TDD funcional | ✓ | `red-native.xml:1`: fallo real del lifecycle por pnpm anidado ausente, antes del cambio productivo; exit1, UTC y argv registrados. GREEN posterior exit0. Los errores posteriores del capturador y la expectativa del separador están cualificados como correcciones del test. |
| Constitución explícita | ✓ | Runtime bajo el proyecto y rechazo de destinos alterados: `scripts/pnpm.py:139`, `:157`; conforme a `docs/CONSTITUTION.md:25`. No se declara cierre sin verificación, conforme a `:33`. |
| Verificación de tareas cerradas | ✓ | T-08 permanece **en-progreso**, con seis CA abiertos (`tasks.md:280`, `:294`). No hay cierre que requiera señalar «verificación declarada sin evidencia». La suite del componente consta ejecutada: **55 passed**, exit0, JUnit y recibo actuales. |
| Generados y documentación E2/E3 | No aplica | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar `export-interop.py --check`. No cambia contratos ni el cliente generado. |

**T-08 → criterios de aceptación globales**

Aquí **✗ significa pendiente**, no defecto imputable a esta entrega parcial.

| Criterio | Estado | Referencia |
|---|---|---|
| Tokens, temas, preferencias y tipografías | ✗ Pendiente | `tasks.md:295` |
| Navegación y reproductor fuera de páginas | ✗ Pendiente | `tasks.md:296` |
| Cliente tipado, SSE y conexión directa | ✗ Pendiente; esta corrección acredita únicamente el transporte del gestor | `tasks.md:297` |
| Textos desde `messages/es.json` | ✗ Pendiente | `tasks.md:298` |
| Playwright, stack y smoke E2E | ✗ Pendiente | `tasks.md:299` |
| Dockerfile/Compose, URLs y SSE reales | ✗ Pendiente | `tasks.md:300` |

La prueba positiva utiliza Node/pnpm oficiales con un sentinel de aplicación controlado; los mocks de límites están identificados por separado. **No acredita generación canónica, UI, build, Docker/Linux ni E2E.** Mi comprobación fue de lectura y contraste de evidencias; no reejecuté suites, regeneré archivos ni modifiqué el ledger. QA independiente sigue pendiente.