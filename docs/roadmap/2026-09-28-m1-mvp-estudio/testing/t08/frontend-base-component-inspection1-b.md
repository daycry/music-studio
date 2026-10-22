| Criterio | Resultado | Fichero:línea y escenario concreto |
|---|---|---|
| Compatibilidad SSE | **Important · B-01** | `apps/web/lib/events.ts:14` y `:18`: al suscribirse a `/api/events`, un evento válido `{id:1,type:"job.progress",ts:"…",data:{…}}` nunca llega a `receive`. Si lleva `event: job.progress`, falta el listener; si llega como `message`, se descarta por exigir `seq`, `job_id` y tipos de engine. Pérdida silenciosa de eventos del contrato global de `convenciones.md` §3. Evidencia estática; la UI todavía no consume este cliente. |
| Build mediante entrada canónica | **Important · conocido, fuera del ownership** | `scripts/pnpm.py:250`: el entorno saneado no proporciona la caché nativa que necesita SWC. El comando original `scripts/pnpm.ps1 --filter web build` terminó con **exit 1 / ERR_SWC_NATIVE_CACHE**. El build directo del actor con entorno privado no acredita este recorrido. Fallo pendiente que requiere una corrección acotada aparte. |
| Ruta inexistente traducida | **Minor · B-02** | `apps/web/app/layout.tsx:14`: una URL inexistente muestra la página automática inglesa dentro del layout castellano. Confirmado en el archivo original `derived-next-before/server/app/_not-found.html:1`. Falta fuera de los 30 paths autorizados; la cualificación de entrega no resuelve el comportamiento. |
| API health, cancelación y respuestas tardías | Sin defectos detectados | `apps/web/lib/api.ts:5`; `apps/web/app/system/page.tsx:12`. |
| Tema, almacenamiento bloqueado y limpieza | Sin defectos detectados | `apps/web/components/ThemeProvider.tsx:11`; `apps/web/lib/theme.ts:5`. |
| Navegación y persistencia del dock | Sin defectos detectados | `apps/web/components/StudioShell.tsx:10`; `apps/web/app/layout.tsx:17`. |

**0 Critical; 2 Important —uno conocido externo—; 1 Minor.**

Verificación propia exclusivamente de lectura: **30/30 fuentes coinciden con el freeze**. El JSON oficial actual confirma **100 % de statements y branches en cada uno de los 12 módulos runtime cambiados**, sin exclusiones; JUnit registra **133 PASS = 112 previos + 21 nuevos**. Revisados argv, UTC, logs, JUnit y snapshots de los RED funcionales; los fallos de imports, transporte y fixtures no cuentan como RED de producto.

No ejecuté builds, tests ni navegador. Las pruebas de fetch/EventSource usan dobles; no acreditan SSE real ni `Last-Event-ID` en red. **T08 completo, Docker, E2E y shadcn permanecen pendientes.**