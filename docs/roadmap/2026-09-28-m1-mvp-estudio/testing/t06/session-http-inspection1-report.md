# Sesión HTTP — revisión de componente 1

0 Critical · 0 Important · 1 Minor B-01: DELETE previo al lifespan accede a registro ausente y devuelve500 sinno-store. Root corregirá tras terminar el freeze de QA SQL; T06 permanece abierta.

## Lente A

**Lente A: 0 Critical · 0 Important · 0 Minor en la unidad HTTP revisada. T-06 permanece abierta.** Los ocho archivos actuales coinciden por SHA-256 con el freeze.

| Tarea → criterio | Resultado | Evidencia `fichero:línea` |
|---|---|---|
| T-06 → sobre de eventos y keep-alive cada 15 s | ✗ Pendiente como criterio completo; esta unidad no implementa transporte SSE | `tasks.md:230`; `apps/server/app/event_routes.py:150` registra únicamente bootstrap/revoke |
| T-06 → replay con `Last-Event-ID` y recuperación de jobs activos | ✗ Pendiente; no se declara cumplido | `tasks.md:231`; estado `en-progreso` en `tasks.md:218` |
| T-06 HTTP → bootstrap con propietario local real, único y activo, revalidado antes de emisión | ✓ | `event_routes.py:20`, `event_routes.py:118`; `test_session_http.py:66`, `:310`, `:436` |
| T-06 HTTP → headers únicos, body vacío y lectura acotada; rechazo de query y credenciales ajenas | ✓ | `event_routes.py:77`, `:87`; `test_session_http.py:131`, `:150`, `:487` |
| T-06 HTTP → Host/Origin y preflight específicos por ruta | ✓ | `security.py:19`, `:98`; `test_session_http.py:106`, `:238`, `:270`, `:400` |
| T-06 HTTP → revocación efectiva, 204 vacío, repetición/expiración inválidas y `no-store` | ✓ | `event_routes.py:138`; `test_session_http.py:66`, `:165`, `:197`, `:284` |
| T-06 HTTP → factoría sin efectos de runtime y cierre del registro | ✓ | `main.py:33`, `:89`; `test_session_http.py:329`, `:354`, `:379` |

| Comprobación transversal | Resultado |
|---|---|
| Alcance | ✓ Los ocho archivos corresponden a `tasks.md:224` y a la secuencia del plan (`improvement-plan.md:67`), concretada por ADR-0058. Ninguna exclusión de usuario oculta producción. |
| Tests y cobertura | ✓ Lectura de los tests contrastada con JUnit: **307 PASS, 0 failures/errors/skips**. Cobertura WHOLE actual, líneas+ramas: `main` **96,9697 %**, `security` **98,6111 %**, `event_routes` **98,0392 %**, `errors` y `api_models` **100 %**; cero exclusiones. Hashes RAW/JSON coinciden con el recibo. |
| Constitución explícita | ✓ Sin violaciones encontradas de `docs/CONSTITUTION.md:33` —estado/verificación—, `:35` —code-first—, `:41` —Host/Origin— y `:42` —secretos—. |
| Verificación de tareas cerradas | N/A: este diff no cierra ninguna tarea. La verificación SSE de `tasks.md:227` sigue pendiente; no la ejecuté para sustituir evidencia. |
| Generados y compatibilidad | ✓ OpenAPI final equivale estructuralmente a la propuesta previa; tipos contienen los headers obligatorios. Evidencia conservada de export `--check` y typecheck con exit 0. **Ejecutado por este revisor:** API-contract `--diff` contra preimagen, **exit 0**, «0 cambio(s) ROMPEDOR(ES) de 2 total(es)». |
| Interop E2/E3 | N/A: el diff no toca `commands/`, `agents/` ni `hooks/`. |

Los RED funcionales conservados acreditan emisión, límites de petición, sintaxis de preflight y bootstrap previo al lifespan. **No acreditan RED independiente para cada assertion adicional**; no concedo TDD completo por criterio.

Pruebas ejecutadas por el productor: ASGI/SQLite/registro real, con cola ajena sustituida; h11 en proceso. No equivalen a sockets, Docker, navegador, QA independiente ni aceptación completa de T-06. Las dos ✗ anteriores son pendientes declarados, **no gaps introducidos por esta entrega parcial**.

## Lente B

**0 Critical · 0 Important · 1 Minor.**

| Criterio | Resultado | Fichero:línea y escenario concreto |
|---|---|---|
| Estado previo al lifespan | **Minor B-01** | [event_routes.py:142]([ruta local]/apps/server/app/event_routes.py:142): `DELETE /api/session`, con Host/Origin válidos, body vacío y token `wrong`, accede a `session_registry` inexistente. Lanza `AttributeError` y devuelve **500 INTERNAL sin `Cache-Control: no-store`**, en lugar de un rechazo controlado. |
| Entradas ambiguas y preflight | Sin defectos adicionales | `event_routes.py:77–118`, `security.py:98–123`. |
| Emisión, revocación y cleanup | Sin defectos adicionales | `event_routes.py:121–147`, `main.py:68–97`. |
| Contratos y compatibilidad | Sin defectos adicionales | `api_models.py:18`, `errors.py:7`, OpenAPI y tipos generados. |

**Prueba propia:** B-01 reproducido mediante la aplicación real en ASGI, íntegramente en memoria y sin lifespan, sockets ni escrituras.

**Evidencia de entrega cotejada:** ocho fuentes coinciden con el freeze; JUnit registra 307 PASS; cobertura oficial por módulo completo entre 96,9697 % y 100 %, cero exclusiones y hashes RAW/JSON coincidentes. Los RED documentados tienen argv, UTC y fallos funcionales; no acreditan RED independiente por cada criterio. SSE y T-06 completos quedan fuera de esta revisión.

## Lente C

**Sin hallazgos.** Gaps: **0 Critical · 0 Important · 0 Minor**.

Alcance: los ocho archivos de `t06-session-http-inspection1/scope.diff`; sus fuentes actuales coinciden con los ocho SHA-256 del freeze. El selector activa C por el patrón `session` en `apps/server/tests/test_session_http.py`. `<base>` no contiene un commit concreto: la revisión corresponde al diff capturado de la entrega.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin hallazgos. Consulta SQLAlchemy con propietario definido internamente; sin nuevos ejecutores de comandos o plantillas. | `apps/server/app/event_routes.py:20` |
| Autenticación y sesión | ✓ Cabeceras únicas y acotadas; bootstrap exige valor `1`; revocación valida la credencial en el registro real. | `apps/server/app/event_routes.py:77`, `:118`, `:138` |
| Host, Origin y CORS | ✓ Host permitido y loopback; Origin exacto; preflight restringido por ruta, método y cabecera. | `apps/server/app/security.py:42`, `:57`, `:98` |
| Secretos y exposición de credenciales | ✓ Sin secretos productivos hardcodeados. Respuestas de sesión con `no-store`; errores finitos sin eco de entradas. La cadena del test es una credencial ficticia. | `apps/server/app/security.py:26`; `apps/server/app/errors.py:22`; `apps/server/tests/test_session_http.py:42` |
| Permisos y autorización | ✓ El cliente no selecciona propietario. Se exige usuario local activo único y se reconsulta antes de emitir sesión. | `apps/server/app/main.py:46`; `apps/server/app/event_routes.py:124` |
| Deserialización insegura | ✓ Sin nuevos mecanismos de deserialización insegura; las rutas rechazan body y query. | `apps/server/app/event_routes.py:87` |
| Path traversal | ✓ Sin rutas de filesystem derivadas de entradas nuevas del cliente. | `apps/server/app/event_routes.py:118` |
| SSRF | ✓ Sin solicitudes salientes ni destinos controlables introducidos. | `apps/server/app/event_routes.py:20`, `:118`, `:138` |

No identifico un escenario concreto de explotación introducido o reabierto; no asigno CWE sin defecto demostrado.

Evidencia del revisor: lectura estática y cotejo de hashes, recibos, stdout y JUnit existentes. La entrega registra **307 pruebas, cero fallos/errores/skips**, con cobertura WHOLE individual de los cinco módulos entre **96,9697 % y 100 %**, cero exclusiones. No ejecuté suites ni probes. Las pruebas ASGI y el parser h11 en proceso no acreditan sockets, uvicorn ni navegador. Este resultado no cierra T06 ni acredita el transporte SSE pendiente.

## Lente D

**Sin hallazgos de rendimiento.** 0 Critical · 0 Important · 0 Minor.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| N+1 | `apps/server/app/event_routes.py:25,129` | Una consulta por bootstrap, fuera de bucles, con `LIMIT 2` y búsqueda por nombre único. |
| Bloqueos síncronos | `apps/server/app/event_routes.py:108,129` | E/S SQL delegada a `to_thread`; recepción asíncrona limitada a una llamada y 1 s. |
| Trabajo repetido evitable | `apps/server/app/event_routes.py:17,40,133` | Patrón compilado al importar; schemas construidos al registrar rutas; una serialización por respuesta. |
| Complejidad con volumen | `apps/server/app/event_routes.py:132,144`; `apps/server/app/security.py:47` | Registro limitado a 32 sesiones y peticiones de sesión a 128 headers. No crece con canciones ni jobs. |
| Activación del selector | `apps/server/app/main.py:95` | El bucle de handlers ya existía; el diff no introduce esperas por elemento. |

Revisado el diff completo de ocho archivos del paquete `scope.diff`; sus hashes coinciden con las fuentes congeladas. Evidencia estática: sin ejecutar suites ni cargas. Los artefactos de entrega confirman 307 pruebas y cobertura WHOLE ≥96,97 % por módulo, sin exclusiones; no constituyen mediciones de rendimiento ni aceptación de T-06/SSE.

