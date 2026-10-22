# Verificación actual de T-06 — suite SSE y sesión HTTP

Fecha: 2026-10-10

Comando ejecutado con el intérprete gestionado:

```powershell
.venv\Scripts\python.exe -m pytest apps/server/tests/test_dispatcher_events.py apps/server/tests/test_event_dtos.py apps/server/tests/test_event_snapshot.py apps/server/tests/test_session_http.py apps/server/tests/test_sse_bus.py apps/server/tests/test_sse_frames.py apps/server/tests/test_sse_http.py -q --basetemp=.cache/pytest/t06-current
```

Resultado: **250 passed in 52.49s**. No hubo fallos ni skips.

La ejecución cubre el bus de eventos, sobres, snapshots, sesión HTTP, frames SSE, endpoint SSE y dispatcher de eventos desde el árbol actual. La suite es una verificación CPU reproducible; no sustituye la revisión adversarial ni la QA de integración Docker/E2E exigida por T-06.
