# Entradas web — revisión2

A/B/C: **0Critical/0Important/0Minor** nuevos. Hallazgos previos corregidos; QA independiente siguiente. No aceptaciónT08/M1, WindowsSWC niCompose/E2E.

### A

**Lente A · revisión 2: 0 Critical · 0 Important · 0 Minor nuevos.** Conforme para la unidad acotada; **no acredita el cierre de T-08**.

Leídos el diff completo, los cuatro ficheros actuales, el brief, el plan, el ledger y la constitución. Comprobé mediante lectura y hashes que las cuatro fuentes coinciden con el freeze y con las copias anteriores a la ejecución final. No ejecuté suites ni modifiqué archivos.

| Tarea → criterio de la unidad revisada | Resultado | Evidencia fichero:línea |
|---|---|---|
| T-08 → `integrity: null/int` produce `INVALID_LOCK`, CLI 2 y ninguna publicación | ✓ | `scripts/fetch_web_dependencies.py:230`; cuatro combinaciones biblioteca/CLI y comparación antes/después en `tests/test_fetch_web_dependencies.py:44`. B1-01 corregido. |
| T-08 → fixtures usan entradas actuales sin depender del historial privado | ✓ | `tests/test_fetch_web_dependencies.py:15`, `:33`, `:82`; `tests/test_web_build_inputs.py:13`, `:36`, `:79`. ROOT1-02 corregido. |
| T-08 → bootstrap físico de 586 archivos, faltan exactamente 23, sin destino publicado | ✓ | `tests/test_fetch_web_dependencies.py:233`: comprueba conjunto copiado, conserva versiones transitivas alternativas y mantiene rechazo y ausencia de destino en `:251–253`. |
| T-08 → selección por nombre **y versión solicitada** | ✓ | `tests/test_fetch_web_dependencies.py:204`, `:225`. Evita omitir también PostCSS 8.5.23 cuando el directo es 8.5.29. |
| T-08 → alcance declarado corresponde al plan | ✓ | Tres ficheros modificados, todos declarados en `tasks.md:286`; coherentes con los prerrequisitos de web/Docker de `improvement-plan.md:41`, `:52`. Scope: 3 dentro, 0 fuera. |
| T-08 → tests y cobertura actual suficiente | ✓ | JUnit final: **66 pruebas, 0 fallos, 0 errores, 0 skips**, exit 0. Misma ejecución: fetch **327/349 = 93,6963 %**; contexto **160/176 = 90,9091 %**, ambos completos y con **0 exclusiones**. Contrastados argv, configuración, JSON y rutas de `.coverage` cruda. |
| T-08 → principios explícitos de la constitución | ✓ | Sin infracciones nuevas de confinamiento (`docs/CONSTITUTION.md:25`), estado/verificación (`:33`) ni contratos generados (`:35`). |
| T-08 → verificación de una tarea cerrada | ✓ | No hay tarea cerrada en este diff: T-08 permanece `en-progreso` en `tasks.md:280`. Las verificaciones completas de `:289–291` siguen pendientes; no las suplí. |
| T-08 → E2/E3 interop | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador. |

Los criterios completos de T-08 conservan este estado:

| T-08 → criterio de aceptación | Acreditado por esta entrega |
|---|---|
| Tokens, temas, preferencias y tipografías (`tasks.md:294`) | ✗ — fuera de esta unidad |
| Navegación y reproductor persistente (`:295`) | ✗ — fuera de esta unidad |
| Cliente tipado y SSE (`:296`) | ✗ — fuera de esta unidad |
| Textos desde `messages/es.json` (`:297`) | ✗ — fuera de esta unidad |
| Playwright, stack, seed y humo E2E (`:298`) | ✗ — pendiente |
| Docker/Compose, URLs, resolución interna y SSE (`:299`) | ✗ — pendiente |

Estos ✗ son límites de acreditación de una tarea abierta, no defectos nuevos del diff.

**TDD y custodia:** el RED original del guard muestra cuatro `AttributeError` antes del cambio; los fallos por historial ausente acreditan la reparación de fixtures, no un RED funcional de producto. Fix2 registra RED focal exit 1 a `2026-10-08T20:36:25Z`, GREEN exit 0 y final exit 0. Se conserva la limitación histórica de copias RED reconstruidas y **CLI96670 con exit desconocido**; el CLI 0 actual pertenece exclusivamente a fix2.

**Gaps nuevos: ninguno.** QA independiente y aceptación completa de T-08/M1 siguen pendientes.

### B

**Sin defectos de corrección en el diff revisado.** 0 Critical · 0 Important · 0 Minor.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| Inputs inválidos | `scripts/fetch_web_dependencies.py:230` | ✓ `integrity` null/int se rechaza antes de escribir; B1-01 corregido. |
| Fixtures independientes del historial | `tests/test_fetch_web_dependencies.py:16`, `tests/test_web_build_inputs.py:13` | ✓ Entradas actuales verificadas; ROOT1-02 corregido. |
| Selección por versión y rechazo incompleto | `tests/test_fetch_web_dependencies.py:229` | ✓ Omite 23 archivos exactos, conserva versiones transitivas y comprueba 586 copias físicas. |

Verificación del revisor: lectura completa del diff y cuatro fuentes, hashes coincidentes con freeze y fuentes del productor. Evidencia entregada contrastada: 66 PASS, cobertura completa 327/349 y 160/176, cero exclusiones; RED funcional de selección anterior al GREEN.

No repetí suites ni ejecuté pruebas nativas. Se conservan las limitaciones históricas de custodia/TDD y el exit desconocido de fix1. Este dictamen se limita al diff; no acredita T08 completo.

### C

**Lente C: sin hallazgos.** 0 Critical · 0 Important · 0 Minor.

Revisado el diff completo suministrado: tres ficheros modificados y cuatro fuentes actuales verificadas por SHA-256 contra el freeze y las copias previas a la ejecución final.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| Inyección SQL/comando/plantilla | `scripts/fetch_web_dependencies.py:230` | ✓ El guard de tipo no introduce ejecución ni nuevos intérpretes. |
| Autenticación y sesión | `scripts/fetch_web_dependencies.py:230` | ✓ Sin cambios en mecanismos de autenticación o sesión. |
| Secretos hardcodeados | `tests/test_web_build_inputs.py:39` | ✓ Sin credenciales añadidas; copia selectiva de entradas explícitas. |
| Deserialización insegura | `scripts/fetch_web_dependencies.py:230` | ✓ Rechaza SRI no textual antes de procesarlo; no añade deserialización ejecutable. |
| Path traversal | `tests/test_fetch_web_dependencies.py:38`; `tests/test_web_build_inputs.py:45` | ✓ Las nuevas lecturas usan los controles existentes de confinamiento; no se relajan. |
| SSRF | `tests/test_fetch_web_dependencies.py:20`; `tests/test_web_build_inputs.py:18` | ✓ Prerrequisitos locales verificados, sin adquisición automática ni nuevas solicitudes. |
| Permisos/autorización e integridad | `tests/test_web_build_inputs.py:68`; `tests/test_fetch_web_dependencies.py:231` | ✓ Herramientas verificadas contra pins; selección por nombre y versión sin alterar la autoridad del runtime. |

**Evidencia:** revisión estática y cotejos de archivos ejecutados por este revisor; no ejecuté suites ni pruebas de explotación. Los originales del productor acreditan 66 PASS y cobertura completa por fichero: fetch 327/349 (93,6963 %) y webinputs 160/176 (90,9091 %), sin exclusiones.

El RED de fix2 acredita la corrección del fixture por versión, no un RED del producto. La salida del CLI antiguo de fix1 sigue desconocida. C fue suplementaria por decisión de root; el selector automático devolvió C=false. Este dictamen no acredita el cierre de T08/M1 ni amplía aprobaciones anteriores.