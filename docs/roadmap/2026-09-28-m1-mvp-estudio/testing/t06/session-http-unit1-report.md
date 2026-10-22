> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Entrega HTTP de sesión — revisión de Root pendiente

POST /api/session/bootstrap y DELETE /api/session implementados en el alcance exacto de ocho archivos. Sólo consulta de User para fijar el ULID local activo en lifespan y revalidarlo antes de emisión. Registro protegido sin cambios: RNG stdlib, TTL8h, capacidad32, validación y revocación directas; cierre en cleanup existente. CORS especial por path/método/header; Host interno rechazado en sesión. Body: un receive con presupuesto1s, sin acumulación, query y framing ambiguo rechazados. Sin cookies ni credenciales en logs.

## Evidencia actual

- runs/final-baseline6: **307 PASS**, cero failures/errors/skips, 125 puros protegidos y 74 nuevos HTTP. Un SAWarning procede de una fixture antigua con MagicMock de engine; no se editó la fixture ni código de cola.
- WHOLE por cada módulo, una sola ejecución actual; datos brutos y JSON conservados. Sin exclusiones, extracción, medias ni unión histórica.

| Módulo | Líneas | Ramas | Oficial líneas+ramas | Excluidas |
|---|---:|---:|---:|---:|
| apps/server/app/api_models.py | 11/11 | 0/0 | 100.000000% | 0 |
| apps/server/app/errors.py | 12/12 | 6/6 | 100.000000% | 0 |
| apps/server/app/event_routes.py | 79/80 | 21/22 | 98.039216% | 0 |
| apps/server/app/main.py | 112/114 | 16/18 | 96.969697% | 0 |
| apps/server/app/security.py | 50/50 | 21/22 | 98.611111% | 0 |

- Contrato propuesto privado validado y comparado antes del código: proposal-lint/proposal-diff exit0. Final equivalente EXACTAMENTE al JSON propuesto. Export code-first, generación locked pnpm, export--check, lint/diff finales, typecheck con incremental=false y ruff/format acotados exit0. engine-v1 byteexact confirmado contra Root.
- Viejos tests/fixtures originales protegidos intactos. Copias privadas cambian sólo dos directorios de fixtures, con paridad AST normalizada en baseline-parity.json. Aliases privados cargan los mismos módulos productivos para los125, sin sustitución de autenticación. Nueva cola fake sólo en nuevos tests HTTP; viejos lifecycle conservan su runtime.

## RED reales conservados

- RED: test_issue_validate_revoke falló en emisión real registrada:503 en vez de200 · 2026-10-09. runs/red-issue.
- RED: rechazo de body/query/credenciales ajenas y permiso de preflight:503 en vez de422,400 en vez de200; no-store ausente en rechazos existentes · 2026-10-09. runs/red-request-boundary. Los12 casos ya verdes no cuentan como RED.
- RED: test_preflight_invalid_syntax:200 en vez de400 para controles y NBSP · 2026-10-09. runs/red-preflight-syntax.
- RED: test_bootstrap_before_lifespan_is_unavailable:500 en vez de503 · 2026-10-09. runs/red-unstarted.
- RED de compatibilidad existente: los tests antiguos de health/error encontraron _IncludedRouter sin path al recorrer app.routes. runs/final-baseline5. Se sustituyó include_router por add_api_route, sin tocar asserts antiguos.

No se denomina RED del producto a fallos de import/colección/configuración ni a las dos fixtures nuevas que violaban FK/identidad/CHECK. El historial íntegro se conserva en runs. No se acredita RED independiente de cada assertion adicional de owner/lifecycle/expiry: esas pruebas acreditan comportamiento final, no un ciclo TDD completo por criterio. TDD n/a: propuesta y artefactos estáticos generados.

## Límites explícitos

TCB: SO, Python gestionado/stdlib y dependencias .venv existentes, herramientas locked Node/pnpm y node_modules. Fuentes productivas/tests/helpers y copias antes de los hijos en cada runs/*/before. Los padres iniciales PowerShell/env.ps1/python--version no tienen PID/argv nativos íntegros:UNKNOWN. Linter inicial de propuesta no se capturó antes del hijo:UNKNOWN; el linter final sí. El primer ruff format no usó --no-cache: mutaciones exactas del caché compartido de proyectoUNKNOWN; siguientes llamadas aisladas o --no-cache. Ningún dato de uso del proveedor original disponible: modelo/tokens/EUR/horasIA=NULL, sin estimaciones.

Parser real h11 sin sockets: Host duplicado falla con hint400; Origin duplicado permanece para ASGI. No equivale a un servidor vivo: transporte/socket/uvicornUNKNOWN. Hijos Python y Node directos esperados con PID/UTC/exit/stdout/stderr; descendencia interna cmd/Node del pnpmUNKNOWN. Observación final de threads: cero nuevos vivos; inventario OS de descendientesUNKNOWN. No GPU/Docker/WSL/browser/E2E/red/instalaciones, ni full1029/original801, ni cierre de tarea/hito. No docs/ADRs/ledger/Git/medidor modificados. Revisión fresca, Nemesis y QA corresponden a Root.

Recibos: receipt.json, actor-command-accounting.json, actor-protected-check.json, actor-owned-after.json, owned.diff, whole-five-current.json y noncli-inventory.json. Los cuatro nombres CLI reservados y los mapas previos de Root se preservan.

DONE_WITH_CONCERNS: límites de TDD por criterio y custodia/observaciones UNKNOWN declarados; pendiente revisión fresca, Nemesis y QA de Root.
