**Lente A · inspección de componente 2: 0 Critical / 0 Important / 0 Minor nuevos.** Resultado limitado a los seis ficheros congelados de T-08. **No acredita T-08 completa ni sustituye la QA nativa 2.**

| Criterio de revisión | Resultado | Evidencia |
|---|---|---|
| 1. Tareas hechas realmente implementadas | ✓ | T-08 permanece `en-progreso`, con seis CA abiertos: [tasks.md](../../../../../docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:280). Esta entrega no declara su cierre. |
| 2. Alcance del plan y `Archivos` | ✓ | Los seis paths corresponden a los prerrequisitos portátiles y temporales propios declarados en `tasks.md:286`, dentro de la fase web de `improvement-plan.md:41`. `scope.json` registra seis dentro de alcance y ninguno fuera; su diff coincide con esos paths. |
| 3. Tests y cobertura | ✓ | Lectura de ambos módulos canónicos y sus aserciones. JUnit actual: **93 PASS / 1 skip**, cero errores/fallos. Igualdad AST comprobada de las 28 funciones originales, incluyendo parametrizaciones. Cobertura completa por fichero detallada abajo. |
| 4. Constitución explícita | ✓ | El confinamiento de rutas cumple `docs/CONSTITUTION.md:43`; conservar T-08 abierta respeta `:58`. Las herramientas Windows son prerrequisitos locales; no se presentan como despliegue Docker del producto (`:31`). Sin violación observada en este diff. |
| 5. Verificación de tareas cerradas | ✓ | No hay tarea cerrada en esta entrega. Las verificaciones web de `tasks.md:289` siguen pendientes; las pruebas portátiles no las sustituyen. No corresponde el gap «verificación declarada sin evidencia». |
| 6. Generados y documentación E2/E3 | No aplica | El diff no toca `commands/`, `agents/` ni `hooks/`; no procede ejecutar `export-interop.py --check`. |

**T-08 → criterios de aceptación del ledger**

`✗ pendiente` indica que esta entrega parcial no acredita el criterio; no constituye un gap de cierre porque sigue abierto.

| Criterio | Resultado | Referencia |
|---|---|---|
| Tokens, temas, preferencias y tipografías | ✗ pendiente | `tasks.md:294` |
| Navegación y reproductor persistente | ✗ pendiente | `tasks.md:295` |
| Cliente tipado, SSE y conexión directa | ✗ pendiente | `tasks.md:296` |
| Textos desde `messages/es.json` | ✗ pendiente | `tasks.md:297` |
| Infraestructura E2E y smoke | ✗ pendiente | `tasks.md:298` |
| Docker/Compose, URLs internas y SSE | ✗ pendiente | `tasks.md:299` |

**T-08 → componente portable y fixtures**

| Comportamiento entregado | Resultado | Código y test leído |
|---|---|---|
| Pins, hashes y manifiesto exacto | ✓ | `scripts/fetch_web_tools.py:73`, `:151`; `tests/test_fetch_web_tools.py:124`, `:583` |
| Rechazo de rutas, colisiones, tipos y límites | ✓ | `fetch_web_tools.py:56`, `:90`, `:115`; `test_fetch_web_tools.py:44`, `:78`, `:94`, `:114`, `:680` |
| Extracción, preservación de destinos y cleanup propio | ✓ | `fetch_web_tools.py:276`; `test_fetch_web_tools.py:286`, `:303`, `:314` |
| Entorno privado, descarga acotada y caché | ✓ | `fetch_web_tools.py:332`, `:386`, `:412`; `test_fetch_web_tools.py:155`, `:369`, `:643` |
| Probes y errores de ejecución | ✓ | `fetch_web_tools.py:454`; `test_fetch_web_tools.py:433`, `:467`. Estos tests usan inyecciones; la evidencia nativa se evalúa separadamente. |
| Namespace real, ownership y limpieza confinada | ✓ | `scripts/test_workspace.py:23`, `:70`, `:85`, `:101`; `tests/test_fixture_confinement.py:24`, `:47`, `:60`, `:99`, `:128` |
| Fixtures comunes y marcador tras fallo Windows | ✓ | `conftest.py:14`, `tests/conftest.py:10`; `test_fixture_confinement.py:135`, `:219` |

La cobertura actual de **cada fichero completo** es **293/315 = 93,02 %**, **83/86 = 96,51 %**, **8/8 = 100 %** y **6/6 = 100 %**, respectivamente; todos con **cero exclusiones**. Cotejé configuración, comando, informe y JUnit: instrumentación antes de importar conftest y combinación de hijos pytest de la misma ejecución.

Para **WEBTOOLS-TDD01**, los nuevos recibos/stdout/JUnit y snapshots muestran fallos de comportamiento antes de reconstruir: digest incorrecto, manifiesto vacío, rechazo ausente, payload inexistente, transporte no invocado y pérdida del marcador. Los 49 `find_spec` históricos, el KeyError de caché y los intentos descartados no cuentan como RED funcional. No encuentro un gap persistente nuevo en esa reconstrucción.

Persisten las limitaciones declaradas en [report.md:25](../../../../../.cache/dev-cycle/m1/t08-tools-tdd-fix1/report.md:25): faltan algunas versiones contemporáneas de tests privados y recibos hijos RED tempranos. **No certifico custodia histórica completa.**

Las sondas nativas entregadas conservan exit 0, **Node v22.23.2 / pnpm 9.12.0** y mapas antes/después iguales: 2933 payloads más dos manifiestos. Como revisor ejecuté únicamente lecturas y comprobaciones en memoria de hashes, AST, JSON y XML; **no repetí suites ni sondas nativas**.