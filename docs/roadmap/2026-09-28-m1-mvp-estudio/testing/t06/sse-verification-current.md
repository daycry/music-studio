# Verificacion actual de SSE y sesiones

Fecha: 2026-10-10

```text
python -m pytest apps/server/tests/test_sse_http.py apps/server/tests/test_session_http.py apps/server/tests/test_sse_bus.py apps/server/tests/test_sse_frames.py apps/server/tests/test_event_snapshot.py apps/server/tests/test_event_dtos.py -q
233 passed in 49.36s
```

La ejecución cubre el bus y frames SSE, snapshot inicial, replay con cursor,
heartbeat, sesiones locales, revocación, expiración y transporte HTTP.
El endpoint mantiene la credencial pública de sesión definida en ADR-0058.
El cierre formal de T-06 todavía requiere revisión adversarial, QA de integración
y el E2E del navegador.
