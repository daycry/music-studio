**Lente A: 0 Critical, 3 Important, 1 Minor.** Revisión acotada a los 30 paths de la base frontend; hashes actuales coinciden con el freeze. T-08 sigue **en-progreso**, con sus criterios abiertos: esta entrega no acredita el cierre completo.

Rutas relativas al repositorio.

| T-08 → criterio de aceptación | Resultado | Evidencia y alcance |
|---|---|---|
| Tokens, temas, preferencias y tipografías | ✓ base | `apps/web/styles/tokens.css:1`, `globals.css:64`, `app/layout.tsx:6`. Tests de tema cubren elección, almacenamiento bloqueado, cambios del sistema y limpieza. Desviación de dimensiones: A-04. |
| Navegación y reproductor fuera del árbol de páginas | ✓ base | `components/StudioShell.tsx:17–25`; `StudioShell.test.tsx:12` comprueba enlaces, cambio de ruta y conservación del dock. Persistencia real en navegador pendiente. |
| API tipada, acceso directo y SSE con reanudación | ✗ parcial | `lib/api.ts:1–7` cumple para `/health`. `lib/events.ts:14` exige el sobre del engine; no acredita el SSE global documentado. A-01. |
| Todo el texto desde `messages/es.json` | ✗ | Rutas propias traducidas; la 404 generada conserva texto inglés. A-02. |
| Infraestructura E2E y smoke | ✗ pendiente | `tasks.md:298`. Fuera de esta unidad aprobada; no se presenta como cumplido. |
| Docker web/server/mock, seed, URLs y SSE | ✗ pendiente | `tasks.md:299`. Fuera de esta unidad aprobada; no hay evidencia Docker/Linux. |

| Comprobación transversal | Resultado |
|---|---|
| Tareas declaradas completadas | ✓ No hay cierre nuevo de T-08; `tasks.md:280` mantiene `en-progreso`. |
| Alcance y `Archivos` | ✓ Los 30 paths pertenecen a `apps/web/`, declarado en `tasks.md:286`, y corresponden a la base prevista en el plan. `scope.json` registra cero paths fuera de alcance. |
| Tests y cobertura actual | ✓ Leídos los tests nuevos. El JSON oficial de la ejecución final acredita **100% individual de statements, funciones y ramas** para los 12 módulos modificados, sin exclusiones. 133 PASS = 112 previos + 21 nuevos; no constituye prueba E2E. |
| TDD | ✓ Los originales RED contienen fallos funcionales y baselines compilables anteriores a la implementación. No cuento errores de transporte, imports ni reparación de fixtures como RED. |
| Constitución | ✗ La 404 incumple el principio explícito de castellano/next-intl, `docs/CONSTITUTION.md:56`. A-02. |
| Verificación declarada | ✗ Build canónico fallido: A-03. No aplica «verificación declarada sin evidencia» de tarea completada, porque T-08 permanece abierta. |
| Interop E2/E3 | N/A: el diff no toca `commands/`, `agents/` ni `hooks/`. |

| Gap | Severidad | Fichero:línea y escenario concreto |
|---|---|---|
| **A-01 — Sobre SSE incompatible con el documentado** | Important | `apps/web/lib/events.ts:14` descarta eventos globales `{id,type,ts,data}` por ausencia de `seq/job_id`, exigidos por el parser. El contrato web está en `docs/arquitectura/convenciones.md:32–33`. Los tests de `events.test.ts:22` usan sobres del engine y no detectan esta incompatibilidad. La reconexión nativa no resuelve el descarte. |
| **A-02 — 404 en inglés** | Important | El artefacto original `.cache/dev-cycle/m1/t08-canonical-build-root1/derived-next-before/server/app/_not-found.html:1` contiene «This page could not be found.» Una ruta inexistente presenta texto fuera de `messages/es.json`, contrario a `tasks.md:297` y **`docs/CONSTITUTION.md:56`**. Está fuera del ownership actual; requiere asignación explícita, pero la cualificación del informe no elimina el incumplimiento. |
| **A-03 — Build por el entrypoint canónico falla** | Important | `scripts/pnpm.py:242–245`; evidencia original en `.cache/dev-cycle/m1/t08-canonical-build-root1/command.json:1` y `stderr-original.txt:1`: wrapper canónico **exit 1**, `ERR_SWC_NATIVE_CACHE`. El build directo con launcher privado exit 0 no cumple la verificación de `tasks.md:290`. Dependencia fuera del ownership de esta unidad; debe permanecer pendiente. |
| **A-04 — Dimensiones del layout distintas de UX §3** | Minor | `apps/web/styles/globals.css:17` fija nav de **144 px** y `:35` dock mínimo de **120 px**; `docs/producto/ux.md:51–54` especifica **64/72 px**. En escritorio la base reserva más espacio que el layout requerido. |

Pruebas ejecutadas por este revisor: lectura y comparación de hashes, recuento del JSON de cobertura y examen de originales/artefactos. No reejecuté build, suites, navegador ni generadores; no modifiqué archivos.