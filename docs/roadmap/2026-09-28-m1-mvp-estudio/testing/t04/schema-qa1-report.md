# QA independiente M1/T04 — primera unidad parcial de esquema

**NEEDS_CONTEXT. Sin aceptación técnica:** falta procedencia autorizada de un toolchain de build licenciado y fijado. La caché usada anteriormente en T02 existe, pero Hatchling1.32.4/pathspec1.1.1/trove-classifiers2026.9.21.13 no tienen fila en docs/legal/licencias.md ni pin en uv.lock; build-system declara Hatchling sin versión. Se conservan metadatos y hashes en needs-context-build-toolchain.json. Según instrucción explícita recibida, no se importó el backend, no se construyó/instaló wheel ni se alteraron dependencias/docs/locks. Root debe resolver esta restricción antes de continuar wheel/Docker y aceptar la dependencia funcional. No pregunta al usuario ni instalación propuesta.

Suite canónica actual completa, nativa gestionada: **522 pass / 3 skip / 0 fail**, 525 casos reales JUnit, exit0. Incluye89+14+71=174 nuevos y ocho ciclos históricos0004, con37 assertions del fixture. Dos ciclos vacío/poblado0004→0005→0004→head y baseline DDL golden en tests actuales pasan. No se sumaron pruebas privadas:0 adicionales. No se debilitaron ni editaron tests: copia byte/AST exacta, layout clone/apps/server conserva ROOT.parents[3]; cwd=clone lleva PHASE hardcoded a rutas privadas dentro de este ownership. No writes en las fases antiguas. Los tres skips reales Windows de symlink se enumeran en canonical-counts.json; los mismos casos Linux están pendientes de Docker y no certificados.

Las pruebas actuales cubren petición/opciones congeladas, SQL/Core/ORM/REPLACE, cursor/terminal, propietario/job/ordinal, max_attempts de modelo, cierre y procedencia de soporte, invalidación/dirty/CAS, conflictos/rollback, snapshot legado sin identidad inventada y backup SQLite restaurado. Pasan los tres casos20/200/405 cuyas assertions observan29/29/32SELECT respectivamente; esta entrega no captura un trace adicional ni presenta fórmulas como medidas nuevas. Calendario SQL imposible/leap/hora24 y lectura tipada UTC se verifican con los71 casos actuales. El recorrido UTCspace solicitado (created/updated/deleted + restore_new) y registry native/wheel/Docker independiente **no ejecutados** al detectar la restricción; se conserva la evidencia root de SQL/project/validate PASS sin date-time checker y no se afirma RFC3339 estricto para clientes externos.

Medición oficial actual sin exclusiones, parser oficial custom-agents1.22.0: tres módulos cumplen80%; la migración0005 cargada dinámicamente por Alembic no fue registrada con source=app y aparece0/18. El finalizador abortó al exigir80; no se declara gate conforme ni fallo funcional de migración. Falta medición corregida del módulo completo, además de wheel/Docker. Incidentes privados de finalización/lectura PowerShell/quoting preservados en CLI sin modificar fuentes. Datos originales intactos (whole-module-gate.json):

| Módulo | Cubiertas/total | % |
|---|---|---|
| apps/server/app/models/__init__.py | 336/338 | 99.41 |
| apps/server/app/snapshots.py | 360/385 | 93.51 |
| apps/server/app/migrations/job_attempt_invariants.py | 184/196 | 93.88 |
| apps/server/app/migrations/versions/0005_job_attempt.py | 0/18 | 0.00 |

Ruff primera llamada --no-cache y formato --check sin caché exit0; exporter canónico privado --check exit0. Ledger-lint0 incoherencias, coverage-check global exit0 conservados; ningún estado se cambia. Gate unidad adapta explícitamente JUnit backend real al formato del gate, sin fabricar E2E. M1 global carece de resultados E2E: NO-VERDE.

Gate unitario:
```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 522,
    "failed": 0,
    "flaky": 0,
    "skipped": 3,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

Gate global M1:
```json
{
  "verdict": "NO-VERDE",
  "reason": "sin resultados: results.json no existe (la ausencia de evidencia es rojo)"
}
```

Fuente congelada10 y protected de root revalidados antes/después exactos; manifiesto clone/copies, argv/cwd/UTC/exits/stdout/stderr/JUnit/cobertura actuales privados. Sin GPU/WSL/Ollama/PDH/UI/pnpm/Git/ledger/meter/knowledge/network ni instalaciones host. Incidentes históricos preservados: fix1 Ruff caché compartida y T03 pnpm descarga automática; no se certifica restricción operacional histórica íntegra. Esta ejecución usa Python-B/uv offline --no-sync --frozen, caches/TEMP privados y primer Ruff sin caché.

No contenedores/imágenes/servicios propios creados; comandos nativos terminados, fixtures privados retenidos. No se realizó limpieza de recursos ajenos ni se certifica su estado global. closed-noncli-inventory.json excluye CLI viva/log/stderr/metadata/final y a sí mismo; root custodia el CLI después de entrega. Modelo/tokens/EUR/horasIA reales NULL; peso3estimado declarado por root antesdispatch. OchoCA T04 abiertos: dispatcher/admisión/SSE/retry/recovery/chains/GPU sin ejecución. No QA completa, task/Git/M1/modelquality ni aceptación implícita por tests verdes.
