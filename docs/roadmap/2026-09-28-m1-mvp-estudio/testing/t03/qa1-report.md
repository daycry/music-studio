# QA independiente M1/T03 — unidad técnica parser/API/contratos

Validación técnica funcional conforme; alcance backend/unitario exclusivamente. No cierra T03, Git, M1, E2E, UI, escucha ni aceptación humana. Incidente de ejecución pnpm explícito más abajo; no se certifica cumplimiento íntegro de la restricción sin descargas.

Suite canónica actual completa: **348 pass / 3 skip Windows**, 351 casos JUnit, exit0. El total esperado353pass no corresponde al inventario canónico: la evidencia histórica354casos incluía cinco pruebas privadas extra y ahora se añaden dos genéricas Unicode. Nombres exactos y saltos en actual-count-reconciliation.json. No selección oculta ni aserción debilitada. Linux no se ejecutó; estos skips no son prueba Linux.

Verificación ledger `pytest apps/server -k lyrics`: **117 pass/234 deselected**, porque selecciona cinco vecinos por nombre además de los112genéricos. Medición específica genérica Python: **112 pass**. TypeScript V8 nativo: **112 pass**, mismo56fixtures y mismo JSON copiado exacto. Los55anteriores mantienen registros/orden; UnicodeNl R03-01 tiene expectativa manual MALFORMED_TAG antes del fix, sections vacío y original/rangos conservados. Tests genéricos Python/TS y todos los tests server copiados byte a byte, sin bootstrap cambiado gracias a la profundidad de directorios espejo. Las únicas adaptaciones TS son cache/output y añadir reporter oficial json-summary. generic-assertion-proof.json y clone-manifest.json conservan evidencia.

Tres criterios originales y sus verificaciones íntegros en unit-fixture/tasks.md/spec.md, con mapeo transparente. Exportador real --check exit0 antes y después de generación; dos **pnpm gen reales** exit0 producen bytes idénticos al tipo congelado. Typecheck real exit0. Test canónico detecta contratos desactualizados/missing y divergencia del publicado; factoría/OpenAPI neutral no configura logging/BD/background/recursos y no lee dotenv/env. Health200, errores403/500, Host/Origin, CORS/privacidad, lifespan/cancelación y cleanup parcial pasan mediante tests canónicos. Dos sondas nuevas403 completan igualdad RFC9457/content-type real antes de lifespan:2pass, sin disco/runtime. No inventa endpoints. /api/generations y SSE de producto no existen; API-02 y E2E-03 completos esperan API futura/editor UI. Los tests de seguridad de paths inexistentes acreditan la frontera antes del routing, no endpoints presentes.

OpenAPI lint de la skill api-contract: exit0, cero errores/avisos. Primer contrato server: --diff anterior n/a, no diff-verde inventado. ADR0019 code-first prevalece. Engine JSON Schema conserva SHA256 1fb5450648ab6eaf04dc3728a9a76a1df4f91dca17332ec6b7d4fbbec8fc5384, 31107bytes, CRLF exacto; no se reescribe. Revisión2 es estática A/B/D0Critical0Important0Minor nuevos, no QA. Scope actual18 tomado de revisión2, selección de paths previa Cfalse/Dtrue conservada como input.

Cobertura oficial actual por módulos ENTEROS, sin exclusiones y cada uno≥80:

| Módulo Python | Cubiertas/total | Cobertura |
|---|---|---|
| apps/server/app/main.py | 78/79 | 98.73% |
| apps/server/app/settings.py | 78/78 | 100.00% |
| apps/server/app/errors.py | 12/12 | 100.00% |
| apps/server/app/api_models.py | 11/11 | 100.00% |
| apps/server/app/lyrics.py | 66/66 | 100.00% |
| scripts/export_contracts.py | 27/28 | 96.43% |

V8 whole lyrics.ts: líneas53/53, statements68/68, funciones5/5, ramas57/62=91,93%. Umbrales nativos80 para todos. Official parsear_pytest/parsear_jest usados sobre JSON reales; no line-diff/prosa/media que diluya requisitos. Reportes completos y datos coverage conservados. Medición inicial source=app omitió los módulos spec-loaded y permanece conservada; focalizados nuevos112parser+testsOpenAPI resolvieron esa falta sin repetir fullsuite verde. Datos clone y canonical CLI separados por ruta; gate usa exclusivamente módulos clone completos iguales a fuentes18.

Ledger lint0incoherencias/0avisos. Coverage-check global exit0 informa T00 sin cobertura declarada (documental; no UI); unidad exit0 conserva el plan original. Unit qa-gate recibe adaptación explícita de JUnit real351 backend, no resultados Playwright fabricados. M1global gate exit1 por ausencia de E2E ejecutados. Spec aprobada/plan borrador/tareas abiertas conservados; ADR0037 separa aceptación técnica, Docker, UI, GPU y escucha. M01/M02/M03 pendientes.

Gate unitario (exit0):
```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 348,
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
Gate global M1 (exit1):
```json
{
  "verdict": "NO-VERDE",
  "reason": "sin resultados: results.json no existe (la ausencia de evidencia es rojo)"
}

```

Incidentes preservados: fullsuite emite aviso de creación de caché privada WinError5, sin fallo funcional. Primer comando TS privado por pnpm falló antes de tests y **intentó instalación automática**, stderr declara downloaded1 y bindingWin32; contraviene la instrucción sinred/descargas. La junction privada apuntaba a node_modules instalado: no se certifica que dependencias instaladas permanecieron intactas; no se revierte nada compartido. Recuperación directa con Node/Vitest ya instalado exit0, sin pnpm installs posteriores. Restricción de fuentes/tests/contratos/locks sí validada exacta antes/después; no confundirla con certificación global de node_modules. constraints-incidents.json mantiene el detalle. Runner inicial exit1 y sus originales conservados, no reejecutado.

Protección:18fuentes exactas antes/después y copias; server/tests/modelos/migraciones/snapshots/contracts/locks protegidos exactos. T09/docs concurrentes fuera de ese inventario, no reclamados intactos. Sin Git/ledger/publicación/meter/goals/subagentes/GPU/Docker/WSL/Ollama/UI/knowledge. Python gestionado env.ps1, uv --no-sync --frozen, Python-B. Recibos nativos argv/cwd/start-endUTC/exit, stdout/stderr/JUnit. Peso2estimado; modelo/tokens/EUR/horasIA reales NULL. CLI de este agente sigue vivo: inventario noCLI excluye originals/stderr/metadata/final; root sellará terminal al retornar.


**Aceptación técnica de raíz:**18fuentes/651artefactos noCLI/terminal0/JUnit351 verificados. Los tres criterios originales cumplen la unidad técnica. Se acepta como dependencia bajoADR0037; se conserva expresamente el incidente de pnpm y no se declara conformidad plena de restricciones ni inmutabilidad de dependencias instaladas. Git/T03cierre/M1/UIpendientes.
