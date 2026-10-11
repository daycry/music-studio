# Revisión de dos lentes — intento 1: T-04

ROOT publica las respuestas de contexto fresco A/B. El estado histórico de este intento es 2 Important y 1 Minor, corregidos y reevaluados en el intento2. C/D auto false; alcance contractual/configuración/CPU, no aceptación de producto M2.

Lente A · intento 1 · diff `581264b6dd62ea102af90360b1976d0940ddb994...HEAD` ∪ cambios sin comitear (27 ficheros).

Revisión por bloques de archivos; schema leído íntegramente como JSON compacto. **0 Critical, 0 Important, 1 Minor.** No bloquea pasar a QA final; no acredita cierre de T-04.

| Criterio (T-XX / objetivo) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| A1 — Cumplimiento y estado de T-04 | ✓ | `tasks.md:163–179`: en-revision, casillas abiertas. No hay cierre anticipado ni reauditoría de T01–03. |
| A2 — Alcance declarado | ✓ | `tasks.md:170`; diff completo de 27 archivos coincide con test, fixtures, schema y baseline. `scope.stdout`: 27 cambiados, fuera_alcance=[], avisos=[], excluidos=[]. |
| A3 — Tests y cobertura | ✓ | `test_creative_contract_compatibility.py:26`: inventario/hash; `:43`: ocho operaciones; `:93–159`: incompatibilidades/versiones/hashes; `:163–236`: lectores históricos y negativos. Ejecución propia: **48 passed**, focal exit0. Cobertura de runtime cambiado n/a: no cambia runtime. |
| A4 — Constitución explícita | ✓ | `docs/CONSTITUTION.md:25`: confinamiento; `:33`: ledger/Verificación; `:35`: code-first; `:42`: secretos. Datos sintéticos, lectores/DTO/SQL/runtime intactos y schema reproducido desde DTO actual. |
| A5 — Verificación declarada acreditada | ✓ | `tasks.md:173`, nota `:1281`; `implementation/commands.json` conserva siete argv/cwd/UTC/exits/reaps auténticos. JUnit original: focal48 y vecinos274, todos sin fail/error/skip. Tarea todavía abierta. |
| A6 — Generado y descripción actualizados | ✗ | Schema reproduce bytes/SHA `af44d416…13693`. Baseline describe resultados comprobados y límites correctamente; su enlace de evidencia QA en `contract-baseline.md:58` está roto: A01 Minor. |
| A6 — Exportación interop | ✓ — no aplica | El diff no toca commands/agents/hooks; no corresponde ejecutar export-interop. |
| Contrato OpenAPI condicional | ✓ — no aplica al diff | No se modifica spec OpenAPI. Evidencia adicional leída: exports base/repeat iguales, lint exit0 y diff exit0/rompedores0. No atribuyo ejecución propia del exporter/lint. |
| T04-CA1 — PostPlan engine histórico | ✓ | Test `:177` conserva DTO, versión y digest; `:187` rechaza versión/extra/authority/shape. Ambos ejecutados dentro de focal48. |
| T04-CA1 — Receta CPU nueva | ✓ | Test `:43`, `:63`, `:83`: codec real, schema wire, envelope y ausencia de autoridad engine CPU. Ocho envelopes cotejados íntegramente con receta/hash correspondiente. |
| T04-CA1 — Lectores manifiesto/song históricos | ✓ | Test `:200–236`: `_validate` y `snapshots.validate` reales, mirrors, seed-only, digest y rechazo de cierre ajeno/incompatible. Ejecutados sin sustituir lectores. |
| T04-CA1 — Diferencia incompatible falla | ✓ | Negativos de codec/schema/PostPlan/manifiesto/song en `:93–236`, ejecutados: extras, forma, identidad, pins, versión y hashes. |
| T04-CA2 — Fixtures sin datos privados | ✓ | `fixtures/creative/README.md:3–28`; índice sintético de22 JSON; inspección de fixtures completos y hashes. IDs/textos/pins ficticios, `runtime_verified=false`; no credenciales reales. |
| T04-CA2 — Compatibilidad contractual, sin custodia ficticia | ✓ | README `:30–35`; baseline `:56–66`: separa forma contractual de audio, custodia, SQLite, modelos, E2E y aceptación real. |
| T04-CA3 — Verificación propia y evidencia entregada | ✓ | 196 payloads del implementer +7 de QA autenticados por bytes/SHA; seis imports originales coinciden con snapshot review. Focal48 y comandos originales comprobados; focal propio48PASS. |
| T04-CA3 — Revisión/QA conformes antes de completado | no verificable todavía | Baseline `:68`, ledger `:163`: revisión en curso y QA final pendiente. Es un gate pendiente explícito, no un cierre indebido. |
| TDD de esta unidad | ✓ | `implementation-return.md`, baseline `:60`, ledger `:1281`: TDD n/a configuración/prosa y regresiones de lectores existentes. Diagnóstico previo no se presenta como RED de producto. |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| A01 | Minor | Enlace roto a los checks originales de QA | T-04 | `docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/contract-baseline.md:58` | `../../../../../evidence-checks.json` resuelve a `.cache/dev-cycle/m2/creative-contract-harness-t04-review1-20261011/evidence-checks.json`, ausente. El archivo auténtico existe en `.cache/dev-cycle/m2/creative-contract-harness-t04-baseline-owner-20261011/evidence-checks.json`; el enlace impide abrirlo desde el candidato. | — |

Lo ejecutado:

- Entorno gestionado con `. scripts/env.ps1`, `uv run --project . --frozen --no-sync --all-packages python -X utf8 -B`.
- Focal propio final mediante `pytest.main`, sin cacheprovider: **48 passed in 0.88s**, focal exit0. Solo la fixture `tmp_path` retorna el directorio snapshot existente; lectores y tests conservados.
- Regeneración del schema en memoria desde `CreativeRecipeV1` y `ModelDescriptor`, con cierre del descriptor y traducción de newline Windows como `prepare.py`: **byteexact**, SHA `af44d416571d50425c65be3d041676ea1713ced4bed9f4b0a1ac5ae0e7113693`, auditor exit0.
- Auditor de manifests/imports: **196+7 payloads auténticos, seis imports auténticos**, exit0.
- Auditor de ocho envelopes: todos sus campos/recipes/hashes coinciden. Auditor de15 enlaces:14 existentes,1 ausente.
- Diagnósticos propios conservados en transcript: primera focal47PASS/1FAIL por `tmp_path` heredado fuera del root privado; comparación inicial LF frente a CRLF falló pese a igualdad semántica. Ambos son preparación del auditor, no fallos atribuidos al candidato. La primera fixture creó únicamente su directorio temporal vacío en `.cache/dev-cycle/m1/t01-implementation/fixtures/f8e6c155fb6747729e5cf49ad046a674`.
- Consulta técnica `knowledge-find.py`: sin resultados; snapshot sin `docs/knowledge/`. No doctrina de memoria aplicada. No suite vecina propia:274PASS procede del JUnit original autenticado.

Fuera de mi lente: las restricciones JSON Schema señaladas por B corresponden a corrección del schema; no atribuyo pruebas propias de esos escenarios ni duplico su hallazgo. C/D auto false. **DONE; no correcciones ni cambios canónicos.**


Lente B · intento 1 · diff `581264b6dd62ea102af90360b1976d0940ddb994...HEAD` (27 ficheros nuevos; leído por ficheros).

| Criterio / objetivo | ✓/✗ | Evidencia |
|---|---|---|
| T-04: regresión mediante lectores reales | ✓ | Focal propio: **48 passed**, exit 0; cinco imports apuntan al snapshot fijado. |
| T-04: fixtures/envelopes íntegros | ✓ | Ocho envelopes contienen receta y SHA exactos; inventario validado por focal; 140 pins sin drift. |
| T-04: esquema refleja restricciones locales del DTO | ✗ | Diez mutantes aceptados por schema y rechazados por codec; cinco controles aislados reproducen el defecto sin reglas relacionales. |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| B01 | Important | Restricciones de cardinalidad emitidas como claves de string | T-04 | `packages/contracts/creative-recipe-v1.schema.json:110` — también `409`, `1280`, `1797` | `tools=[]`, `parents=[]`, tres padres, `ops=[]` y cuatro operaciones producen **0 errores** del esquema. `minLength/maxLength` no restringen arrays. Los DTOs rechazan los casos; controles aislados `CpuSelection` y `SectionMapIntent` también rechazan sin depender de relaciones o hashes. |
| B02 | Important | Límites numéricos emitidos mediante claves desconocidas | T-04 | `packages/contracts/creative-recipe-v1.schema.json:128` — también `207`, `230`, `242`, `746` | `duration_s=0/-1`, `at_s=-1`, `fade_in_s=-1` y duración del asset cero producen **0 errores** del esquema: `gt/ge` no aplican límites Draft 2020-12. Controles aislados de `Crossfade`, `Extend` y `MasterAssetSnapshot` rechazan mediante `ValidationError`. |

Lo ejecutado: entorno gestionado, Python `-X utf8 -B`; focal con `--noconftest -p no:cacheprovider` y fixture `tmp_path` en memoria, sin escrituras → **48PASS**; diez mutantes → `schema_errors=0 / codec=RECIPE_INVALID`; cinco DTOs aislados → `schema_errors=0 / dto REJECT ValidationError`; comparación de los 27 ficheros contra `source.diff` normalizando finales de línea → conforme; ocho envelopes → receta/hash exactos; **140 pins, drift=[]**. Dos sondas iniciales de comparación fallaron por representación de finales de línea; comprobación corregida exit 0. Consulta `knowledge-find` sin aciertos; lente genérica sin persona `test`.

Fuera de mi lente: conformidad documental y enlaces del baseline corresponden a A. Sin aceptación de audio, custodia, E2E ni M1/M2. **DONE: ninguna escritura ni corrección.**
