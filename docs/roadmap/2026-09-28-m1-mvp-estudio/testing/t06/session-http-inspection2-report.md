# Sesión HTTP — revisión de componente 2

0 Critical · 0 Important · 0 Minor. B-01 corregido. La auditoría actual y QA independiente siguen pendientes; no aceptación de T06.

## Lente A

**Lente A — revisión 2: 0 Critical · 0 Important · 0 Minor.** Resultado limitado al fix B-01 de dos ficheros; no acredita el cierre de T-06.

| Tarea → criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| T-06 → DELETE con registro ausente/`None` devuelve error tipado 503 | ✓ | `apps/server/app/event_routes.py:143–149`: guarda mínima y manejo de `SessionError`. |
| T-06 → Registro no iniciado/cerrado conserva su error; respuesta `no-store` | ✓ | `apps/server/tests/test_session_http.py:573–629`: ocho casos con aplicación ASGI real, cuerpo vacío y sin lifespan; comprueban estado, código, cabecera y ausencia de excepción. |
| T-06 → Credencial ausente 401; token incorrecto con registro vivo 401; revocación 204/repetición 401 | ✓ | `event_routes.py:140`; `test_session_http.py:66–83`, `:162–173`, `:622–628`. |
| T-06 → Alcance y `Archivos` | ✓ | Ambos ficheros están declarados en `docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:224`. Diff completo leído; hashes actuales coinciden con el freeze. Las 25 definiciones originales del módulo de tests conservan su AST. |
| T-06 → Tests, TDD y cobertura actual | ✓ | RED causal registrado: **2 fallos `500 == 503` / 6 pass**, antes de la guarda; `tasks.md:1749`. Final2: **315 pass**, JUnit sin errores ni omisiones. Cobertura WHOLE oficial con ramas: `event_routes` **98,11 %**, `main` **96,97 %**, `security` **98,61 %**, `errors` y `api_models` **100 %**; cero exclusiones. JSON, RAW y snapshots de los cinco módulos contrastados. |
| T-06 → Principios explícitos de la constitución | ✓ | Sin violaciones del cambio revisado. Conserva rutas dentro del proyecto (`docs/CONSTITUTION.md:43`), estado canónico y cierre condicionado a verificación (`:58`), contratos code-first (`:62`) y frontera Host/Origin (`:74`). |
| T-06 → Verificación de tarea cerrada | N/A | T-06 sigue **en-progreso** (`tasks.md:218`); ambos CA siguen abiertos (`:230–231`). La verificación `pytest … -k sse` (`:227`) no se acredita mediante los 315 tests de este componente. |
| T-06 → Generados y descripción E2/E3 | ✓ / N/A | No cambia API, esquema ni documentación contractual: la guarda utiliza el 503 ya declarado (`event_routes.py:52`). Evidencia de entrega: `export_contracts.py --check`, exit **0**. Interop **no aplica**: el diff no toca `commands/`, `agents/` ni `hooks/`. |

**CA completos de T-06:** sobre/tipos/keep-alive y recuperación mediante `Last-Event-ID` quedan **pendientes, fuera de la aceptación de este fix**; no son defectos de una tarea declarada completada.

**Gaps:** ninguno. Revisé fuentes y registros mediante lectura, hashes, AST y consulta RAW de cobertura en solo lectura; no ejecuté tests ni código del producto. QA independiente de los 315 casos y seguridad sobre la guarda actual continúan pendientes, como declara `tasks.md:1747`.

## Lente B

**Sin defectos** en el diff completo de dos ficheros de review2.

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Registro ausente o `None` | ✓ Error tipado 503; resuelve B-01 | `event_routes.py:143` |
| Registro no iniciado o cerrado | ✓ Conserva `SessionError`, sin silenciarlo ni devolver 204 | `event_routes.py:146` |
| Credenciales y revocación | ✓ Mantiene validación previa, 204 válido y 401 al repetir | `event_routes.py:140` |
| Regresión del caso corregido | ✓ Ocho escenarios ASGI con cuerpo vacío; verifica código, `no-store` y ausencia de excepción | `test_session_http.py:575` |

**Gaps:** Critical 0 · Important 0 · Minor 0.

Revisión estática de fuentes actuales con hashes coincidentes con el freeze. Evidencia registrada cotejada: RED causal **2 fallos/6 passes**, anterior a la guarda; final2 **315 passes**, cobertura WHOLE de los cinco módulos ≥80 % y cero exclusiones. No ejecuté tests ni código de producto.

Este resultado se limita al fix B-01; no cierra T-06 ni sustituye la QA independiente pendiente.

## Lente C

**Sin hallazgos de seguridad.** Gaps: **0 Critical / 0 Important / 0 Minor**.

Alcance: diff completo de dos ficheros capturado en `t06-session-http-inspection2/scope-fixture`, cotejado con las fuentes actuales y sus SHA-256 congelados. Selector C activado por el patrón `session`.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Autenticación y sesión | ✓ La guarda devuelve 503 sin permitir revocación; se conserva `validate(token)` antes de `revoke`. | `apps/server/app/event_routes.py:140–148` |
| Permisos y autorización | ✓ No introduce autoridad alternativa ni modifica owner, Host, Origin o preflight. | `apps/server/app/event_routes.py:143–146` |
| Inyección SQL/comando/plantilla | ✓ No añade consultas, ejecución de comandos ni plantillas. | `apps/server/app/event_routes.py:143–145` |
| Secretos hardcodeados | ✓ No añade credenciales reales; `"wrong"` y el ULID son datos de prueba. | `apps/server/tests/test_session_http.py:573–586` |
| Deserialización insegura | ✓ El nuevo `json.loads` procesa únicamente la respuesta capturada por el test. | `apps/server/tests/test_session_http.py:628` |
| Path traversal y SSRF | ✓ Ruta de fixtures fija; no incorpora destinos de red ni rutas controladas por solicitudes. | `apps/server/tests/test_session_http.py:17` |

Evidencia **registrada**, no ejecutada por este revisor: RED causal con **2 fallos 500→503 y 6 pases**; final2 JUnit **315 pases**, sin fallos ni skips. Cobertura WHOLE actual de los cinco módulos: **96,97–100 %**, cero exclusiones.

Revisión estática estrictamente readonly. Sin escenario de explotación nuevo identificado ni CWE aplicable a un defecto. Este resultado no sustituye la QA independiente ni cierra T-06.

