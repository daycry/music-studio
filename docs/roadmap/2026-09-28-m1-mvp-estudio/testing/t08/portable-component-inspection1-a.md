**Lente A: sin gaps nuevos de requisitos o constitución en la unidad portable revisada.** Critical: **0** · Important: **0** · Minor: **0**. Esto no acredita T-08 completa.

Revisé las tres fuentes actuales y el diff aislado; sus hashes coinciden con `source-freeze.json`. El alcance corresponde a ADR-0048 y a `Archivos` de T-08.

| Tarea → criterio de revisión | Resultado | Evidencia `fichero:línea` |
|---|---|---|
| T-08 → implementación declarada | ✓ Unidad parcial; tarea `en-progreso`, sin CA cerrados | `tasks.md:280`, `tasks.md:294` |
| T-08 → alcance permitido | ✓ Script, tests y adiciones Node/pnpm autorizados; FFmpeg preservado | `tasks.md:286`; `ADR-0048-herramientas-frontend-portatiles.md:15`; `tools/tools.lock.json:16` |
| T-08 → pins e identidad antes de ejecución | ✓ SHA-256/tamaño, SHA1/SRI de pnpm, identidad y `packageManager` exactos | `scripts/fetch_web_tools.py:74`, `:214`, `:231`; `tests/test_fetch_web_tools.py:137`, `:237` |
| T-08 → rechazo de archivos inseguros antes de extracción | ✓ Inspección completa, límites, rutas, colisiones y tipos especiales | `scripts/fetch_web_tools.py:92`, `:154`; `tests/test_fetch_web_tools.py:73`, `:90`, `:106`, `:122` |
| T-08 → extracción y conservación de destinos ajenos | ✓ Staging propio, comprobación íntegra y rechazo sin sobrescribir destinos existentes | `scripts/fetch_web_tools.py:248`, `:289`; `tests/test_fetch_web_tools.py:282`, `:298`, `:310` |
| T-08 → confinamiento y ejecución portable | ✓ Entorno permitido, rutas privadas y ejecutables absolutos | `scripts/fetch_web_tools.py:345`, `:463`; `tests/test_fetch_web_tools.py:160`, `:320`, `:483` |
| T-08 → comprobación sin descarga/extracción | ✓ Tests negativos y comprobación nativa registrada | `scripts/fetch_web_tools.py:421`; `tests/test_fetch_web_tools.py:365`, `:536`; `native-once.py:28` |
| T-08 → tests y cobertura | ✓ Lectura de los tests; **290/315 = 92,06 %** del módulo completo, **0 exclusiones**, supera 80 % | `coverage-final.json:1`; `green-final-command.json:1`; `green-final.stdout.txt:1` |
| T-08 → constitución explícita | ✓ Sin infracción nueva de confinamiento ni cierre indebido | `docs/CONSTITUTION.md:25`, `:33`; código citado arriba |
| T-08 → verificación de tareas cerradas | ✓ No hay tarea cerrada en este diff. Lint/build/E2E frontend permanecen pendientes | `tasks.md:280`, `:289` |
| T-08 → generado y documentación, E2/E3 | N/A: no cambia `commands/`, `agents/` ni `hooks/`. No corresponde ejecutar exportador interop | `scope.diff:1`, `:1116` |

Los seis CA de producto siguen pendientes:

| T-08 → criterio de aceptación | Resultado |
|---|---|
| Tokens, temas, preferencias y tipografías — `tasks.md:294` | ✗ Pendiente |
| Navegación y reproductor persistente — `tasks.md:295` | ✗ Pendiente |
| Cliente tipado y SSE — `tasks.md:296` | ✗ Pendiente |
| Textos desde `messages/es.json` — `tasks.md:297` | ✗ Pendiente |
| Infraestructura E2E y humo — `tasks.md:298` | ✗ Pendiente |
| Docker web/server/mock — `tasks.md:299` | ✗ Pendiente |

Estas pendientes no son gaps de la unidad parcial autorizada.

**Evidencia independiente del revisor:** cotejé los **2.933 archivos instalados** contra el manifiesto: **0 discrepancias**. Los diez archivos protegidos mantienen sus hashes. Las ejecuciones registradas muestran **74 passed / 1 skipped**, Ruff exit **0**, versiones nativas `v22.23.2` y `9.12.0`, ambas exit **0**; no las repetí.

**Límites preservados:** el RED inicial acredita 49 fallos funcionales y cero errores de colección, pero carece de copia histórica exacta del test y metadatos individuales completos. `red-cache2` sí acredita el fallo funcional por segunda descarga; el `KeyError` anterior no cuenta como RED. Los tests posteriores a GREEN son suplementarios. Sigue declarado el incidente inicial de namespace T03, ya corregido. El skip por privilegios de symlink no acredita rechazo nativo de junction/reparse; tampoco quedan certificados Linux, vigilancia de escrituras de todo el host ni QA independiente. El selector oficial capturado devuelve C/D **false**; la sugerencia del receipt no sustituye ese resultado.