# Verificacion actual de API de dominio

Fecha: 2026-10-10

```text
python -m pytest apps/server/tests/test_domain_routes.py -q
18 passed in 6.34s

python scripts/export_contracts.py --check
engine-v1.json up to date
openapi.json up to date
```

La API de canciones, letras, generaciones, takes, colecciones y sistema mantiene
el contrato exportado. T-07 sigue abierta por la revisión adversarial, el gate de
cobertura y la validación E2E de todas las rutas.
