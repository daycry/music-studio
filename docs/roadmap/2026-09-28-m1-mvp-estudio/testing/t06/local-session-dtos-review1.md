# Revisión de dos lentes — intento 1: registro local y DTOs

**A/B/C:0 Critical · 0 Important · 0 Minor.** D no activada por selector automático. Revisión cerrada, QA independiente pendiente.

Cuatro fuentes actuales exactas,125PASS y ambos módulos completos98,7342%/99,3902%sin exclusiones en la única corrida del productor. La incidencia de caché compartida está conservada y no demuestra corrupción de fuente. Registro/DTOs puros; no autorización HTTP, CORS, UserDB, SQL/feed, builder, cliente ni E2E.

## Lente A

**Lente A · revisión 1: sin defectos en la unidad pura entregada.**  
**Gaps: 0 Critical · 0 Important · 0 Minor.** T-06 permanece abierta; este resultado no acepta la tarea completa.

Alcance revisado: los cuatro ficheros nuevos de `t06-local-session-dtos-unit1`, sus fuentes actuales y evidencias registradas.

| Tarea → criterio | Resultado | Evidencia y límite |
|---|---|---|
| T-06 → Sobre `{id,type,ts,data}`, tipos previstos y keep-alive de 15 s | ✗ Pendiente completo; ✓ parte entregada | `apps/server/app/event_dtos.py:93` valida el sobre `system.status`; `:127` serializa controles. `apps/server/tests/test_event_dtos.py:155` comprueba contenido y wire ID. Esta unidad no implementa los restantes eventos ni heartbeat HTTP. El criterio sigue abierto en `tasks.md:230`. |
| T-06 → Replay con `Last-Event-ID` y recuperación de jobs activos | ✗ Pendiente completo; ✓ formas de snapshot | `event_dtos.py:59` define begin/chunk/end acotados; `:117` exige correspondencia entre cursor final y body ID. Tests en `test_event_dtos.py:171`, `:236` y `:262`. SQL, barrera, feed autorizado y transporte quedan explícitamente pendientes; `tasks.md:231` continúa abierto. |
| T-06/U1 → Registro local, owner fijo, aleatoriedad, TTL y capacidad | ✓ | `local_sessions.py:74`, `:164` y `:201`: owner fijado internamente, `token_urlsafe(32)`, TTL absoluto de 28.800 s, máximo 32 sesiones, purga y rechazo sin expulsar sesiones válidas. Tests en `test_local_sessions.py:42`, `:63` y `:261`. No acredita resolución de User en BD. |
| T-06/U1 → Revocación, cierre y bindings genuinos | ✓ | `local_sessions.py:212`, `:222`, `:237` y `:249`: identidad del registro, epoch y binding; rechazo de referencias copiadas/ajenas y cierre. Tests en `test_local_sessions.py:94`, `:104` y `:112`. |
| T-06/U1 → Validación y errores acotados | ✓ | `local_sessions.py:61`, `:130` y `:157`: entrada ASCII limitada antes del padding, comparación de todos los registros y errores cerrados. Tests en `test_local_sessions.py:136`, `:168`, `:206` y `:238`. La instrumentación verifica llamadas a `compare_digest`; no constituye una medición temporal. |
| T-06/U1 → DTOs cerrados, null, valores finitos y límites de frame | ✓ | `event_dtos.py:22`, `:41`, `:69` y `:127`. Tests de extras privados, tipos, límites y serialización en `test_event_dtos.py:47`, `:62`, `:82`, `:217` y `:236`. El frame registrado mide **21.597 bytes**, incluidos headers. La forma no acredita autorización ni consistencia entre chunks. |

| Comprobación transversal | Resultado | Evidencia |
|---|---|---|
| Implementación frente a estado declarado | ✓ | `tasks.md:218` mantiene T-06 `en-progreso`; ambos CA abiertos. No hay cierre de T-06 que contradiga la entrega parcial. |
| Alcance y `Archivos` | ✓ | Los cuatro paths figuran en `tasks.md:224`. La secuencia del plan, ADR-0058 y `tasks.md:1292` autorizan registro/DTOs antes de HTTP. Scope registrado: cuatro cambios, cero fuera de alcance; configuración sin exclusiones propias. |
| Tests y cobertura actual | ✓ | Lectura de ambos tests completos. Evidencia final: **125 passed**, cero fallos/errores/skips; PID **18044**, exit **0**, UTC **22:49:36–22:49:37**. Cobertura de módulos completos: DTOs **78/79 = 98,7342 %**; registro **163/164 = 99,3902 %**; **cero exclusiones**, una traza actual. |
| TDD conductual | ✓ | Los 22 grupos RED tienen comandos, UTC, PID, exit 1 y fallos funcionales en JUnit. Los errores de imports, selector y fixture están separados. No se afirma RED individual para las 125 parametrizaciones. |
| Constitución explícita | ✓ | Sin infracciones identificadas de `docs/CONSTITUTION.md:32`, `:43`, `:58`, `:62`, `:64` y `:75`. No se modifica una API registrada que obligue a regenerar OpenAPI en esta unidad. |
| Verificación de tareas cerradas | No aplica al cierre | La verificación de T-06 está en `tasks.md:227`; T-06 sigue abierta. Los 125 tests de unidad no sustituyen ese comando ni E2E. |
| Generados/descripciones E2/E3 | No aplica interop | El diff no toca `commands/`, `agents/` ni `hooks/`; no procede ejecutar el exportador. ADR-0058 describe expresamente esta primera unidad pura y sus integraciones pendientes. |

Comprobaciones propias exclusivamente de lectura: hashes actuales coincidentes con el freeze y copias selladas, originales de comandos/JUnit y artefactos de cobertura. **No ejecuté tests ni probes de producto.** La QA independiente sigue pendiente; tampoco hay aceptación HTTP, SQL, navegador o E2E.

## Lente B

**Sin defectos de corrección encontrados.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| TTL, capacidad y colisiones | `apps/server/app/local_sessions.py:164` | ✓ |
| Revocación, cierre y bindings copiados/ajenos | `apps/server/app/local_sessions.py:212` | ✓ |
| Carreras y liberación del lock ante errores | `apps/server/app/local_sessions.py:117` | ✓ |
| Entradas inválidas y fallos de reloj/RNG | `apps/server/app/local_sessions.py:130` | ✓ |
| DTOs estrictos, límites y valores nulos | `apps/server/app/event_dtos.py:22` | ✓ |
| Revalidación anidada, framing y cursor final | `apps/server/app/event_dtos.py:127` | ✓ |

Los cuatro textos actuales coinciden con el diff completo, el freeze y las copias de la corrida final. Evidencia registrada contrastada: 125 PASS; cobertura completa por módulo 78/79 y 163/164, sin exclusiones.

Revisión propia estática y cotejos en solo lectura; no ejecuté suites ni probes funcionales. Este resultado se limita a la unidad pura y no sustituye la QA independiente ni acredita integración HTTP/SQL o cierre de T06.

## Lente C

**Sin hallazgos.** Lente C: **0 Critical · 0 Important · 0 Minor**.

Alcance: cuatro ficheros nuevos del diff congelado de `inspection1`, cotejados por SHA-256 con las fuentes actuales y la entrega. Activación: patrón `sessions` en módulo y tests.

| Criterio | Resultado | Evidencia `fichero:línea` |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin operaciones de este tipo; framing SSE con cursor validado y JSON serializado. | `event_dtos.py:86`, `event_dtos.py:127` |
| Autenticación y sesión | ✓ RNG criptográfico por defecto, TTL absoluto, comparación acotada sin salida temprana, revocación y cierre. | `local_sessions.py:79`, `local_sessions.py:157`, `local_sessions.py:201`, `local_sessions.py:237` |
| Permisos/autorización | ✓ Owner fijado internamente; bindings ajenos, copiados o invalidados no conceden acceso. | `local_sessions.py:164`, `local_sessions.py:212`, `local_sessions.py:222` |
| Secretos y privacidad | ✓ Sin secretos productivos hardcodeados; repr oculta token y errores del registro no reflejan entradas. Exportación de credencial intencionada. | `local_sessions.py:27`, `local_sessions.py:179`, `event_dtos.py:32` |
| Deserialización insegura | ✓ DTOs cerrados y validación anidada antes del framing; sin pickle ni ejecución dinámica. | `event_dtos.py:22`, `event_dtos.py:130` |
| Path traversal / SSRF | ✓ Los módulos nuevos no realizan acceso a archivos ni peticiones de red. | `local_sessions.py:7`, `event_dtos.py:7` |
| Recursos acotados | ✓ Capacidad32, ocho intentos de generación, headers64 y chunks64; límite de frame65536. | `local_sessions.py:24`, `local_sessions.py:61`, `local_sessions.py:171`, `event_dtos.py:74`, `event_dtos.py:136` |

Evidencia propia: revisión estática y cotejos de solo lectura; **sin ejecutar tests ni probes**. Evidencia archivada contrastada:125PASS, cobertura completa por módulo78/79 y163/164, cero exclusiones. Esto no sustituye QA independiente ni acredita la futura integración HTTP, CORS, UserDB o autorización del feed.

