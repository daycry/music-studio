# T-06 - namespace de sesiones

Fecha: 2026-10-10

RED: la coleccion de `apps/server/tests` abortaba con `ModuleNotFoundError: local_sessions`. GREEN: `test_local_sessions.py` usa `app.local_sessions`, pasa **55 tests** y Ruff queda limpio. La coleccion completa de server queda en **1819 tests** sin errores de importacion.
