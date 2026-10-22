> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# B-01: DELETE antes del lifespan

Guarda mínima con getattr y None: SERVICE_UNAVAILABLE tipado; registro no iniciado/cerrado conserva su error propio. Credencial ausente continúa en 401; token erróneo con registro vivo continúa en 401; 204/repetición401 verificados por test original. Sólo event_routes.py y test_session_http.py modificados, más salidas privadas.

Root liberó freeze explícitamente en t04-current-sql-projection-integration-qa1/root-failed-qa-adjudication.json (03:55:26 UTC), antes de toda escritura de fuente. No aceptación de SQL ni de SSE.

RED: apps/server/tests/test_session_http.py::test_delete_unavailable_registry_before_lifespan[wrong-missing] y [wrong-none] fallaron con assert 500 == 503 · 2026-10-09T03:59:00 UTC. runs/red2 contiene fuente, runner, fixtures, argv, PID, UTC, stdout/stderr, exit1 y JUnit. runs/red inicial fue NO causal: httpx body continuación devolvió422, preservado. Test corregido a ASGI real con body vacío completo; sin lifespan ni doble de producción.

GREEN focal: 8 PASS. Ruff inicial detectó catch Exception sólo en test; acotado a AttributeError, sin captura general en producción. Lint2 PASS --no-cache. Format --check PASS. Export --check PASS; OpenAPI/engine-v1/api.d.ts byteexact frente Root. No regeneración.

Baseline final fallido preservado: 305PASS/10FAIL por ausencia STUDIO_TEST_ROOT/STUDIO_QUEUE_TEST_ROOT. Restauración de receta environment original adaptando sólo rutas privadas. Nueva ejecución justificada por fallo material de harness, sin cambio de fuentes: final2 315PASS, 307 originales +8 nuevos. Antes de final2 se precopiaron recursos del mapa original final-baseline6; cobertura actual singletrace WHOLE y cero exclusiones en actor-whole-current.json. No unión histórica. Todas funciones/asserts/params/decorators/timeouts HTTP originales AST iguales salvo constante UNIT adaptada; fixtures baseline AST iguales salvo rutas privadas. 125 puros protegidos byteexact.

Límites y desviación: primer red no causal creó ocho directorios UUID nuevos bajo fixtures de la fase antigua debido a UNIT heredado; no sobrescritura de ficheros existentes; preservados, sin borrar ni ocultar. La ruta se corrigió antes del RED causal. Cierre transitivo de imports previo RED no probado; snapshots iniciales parciales, final2 ampliados al mapa original. Census completo de descendientes OS UNKNOWN; PIDs directos recogidos con wait. No procesos nativos propios/GPU/Docker/UI. Modelo/tokens/EUR/horas IA NULL sin originales del proveedor. Earliestlinter/sharedruffcache UNKNOWN históricos no reescritos. Seguridad del source anterior no acredita la guarda nueva.

Entrega de componente para Root: revisión2 fresca y QA pendientes. Sin ledger/docs/ADR/Git/meters/goals ni aceptación de tarea/hito.
