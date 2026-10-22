# Regresion Windows del ciclo actual

Fecha: 2026-10-10

## Alcance

Se aislaron dos rojos de la suite completa del server que no eran fallos de produccion:

- `test_r02_13_new_dependency_second_connection[artwork]` leia `song.json` sin declarar UTF-8. En Windows la codificacion regional convertia el texto Unicode al comparar el snapshot con SQLite.
- `test_security_sse_allowed_origin_without_fake_endpoint` conservaba la expectativa anterior de `404`, aunque ADR-0058 exige sesion para `GET /api/events`.

## Cambios

- Las lecturas JSON del test de snapshots declaran `encoding="utf-8"`.
- La prueba SSE espera `401` y `SESSION_REQUIRED`, alineada con el contrato vigente.

## Verificacion

```text
pytest apps/server/tests/test_review_fix2_t02.py::test_r02_13_new_dependency_second_connection -q
2 passed

pytest apps/server/tests/test_security_errors.py::test_security_sse_allowed_origin_without_fake_endpoint -q
1 passed

ruff check apps/server/tests/test_review_fix2_t02.py apps/server/tests/test_security_errors.py
All checks passed!
```

La suite completa anterior queda clasificada en `1742 passed, 4 skipped, 6 failed, 68 errors`: los cuatro fallos nativos restantes y los errores de custodia/FFmpeg requieren el runner Linux/Compose o sus variables de recibo; no se han ocultado ni convertido en verdes falsos.
