# QA final independiente — M2 T-04 — 2026-10-11

**VERDE para el harness contractual CPU/configuración/documentación.** Gate oficial exit 0 en Windows y Linux Docker real: 69 focales + 183 recetas + 91 composición = **343 casos únicos**, todos PASS, sin fallos, errores, skips, flaky ni interrupciones. Cada plataforma ejecuta esos mismos 343 IDs: no son 686 casos únicos. Además, tres controles privados del generador pasan en cada plataforma; no se suman a la suite de producto.

T-04 se entrega a ROOT para adopción/cierre condicionado a sus comprobaciones. QA no modifica ledger ni estados. M1/M2 no se aceptan como hitos con esta evidencia. No se ejecutó Playwright, API, A11Y, audio, SQLite, custodia nativa, modelos, GPU ni producción. No se instalaron dependencias. PDF omitido explícitamente por el alcance delegado documental CPU; no se usó navegador.

## Fuentes, ejecución y límites

[Release ROOT](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/release-root.receipt.json) fija 140 fuentes y 27 candidatos, comprobados antes y después. Schema SHA-256 `05ef38f24f178a9294bcdaaf6a8ef122f37b9270ad22972b9c3f4ffd7f9688dc`; test SHA-256 `78921e088d88cf2950a3fedc1f936ddc64bacf11d50c82a54e867fb43f97a931`; índice `7b20e03ea12ac5a1874ef817b61c0ecee38810841bef602d4b554a924a57725c`. [Sello](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/seal-checks.json), [imports Windows](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/windows/imports.json) y [Linux](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/linux/imports.json) prueban seis lectores actuales importados directamente desde el snapshot, sin sustituir lectores/tests. El único ajuste de fixture en memoria retorna el directorio existente del snapshot para tmp_path, dentro de la autoridad léxica real de db.confine_path; no crea ni conecta BD.

Entorno Windows gestionado mediante scripts/env.ps1 y `uv run --frozen --no-sync --all-packages python -X utf8 -B`. [Comando Windows](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/windows.receipt.json) y [comando Docker](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/linux.receipt.json) registran argv/cwd/UTC/PID/exit/reap y SHA de streams. Imagen CPU existente inspeccionada por ID `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`; sin build/pull/retag, UID10001, network none, cap-drop ALL, root y snapshot read-only, tmpfs temporal y output propio. [Retirada](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/container-cleanup.receipt.json) confirma ausencia del UUID del contenedor propio tras --rm. Ningún servicio/ACE/Ollama incumbente intervenido.

Antes de las pruebas se detectó únicamente deriva canónica del ledger: release92094d → actualb4029e. ROOT confirmó su traza review2 añadida después del release; se conservó la preimagen y se utilizó el ledger snapshot fijo. [Contexto](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/ledger-root-context.json). Los restantes guards canónicos permanecen exactos; no se restaura ni escribe el ledger. El fallo inicial de assert por ese contexto fue preparación QA antes de ejecutar casos, no fallo del candidato.

## Verificación propia

| Ámbito | Windows | Linux real | Evidencia |
|---|---:|---:|---|
| T04 focal contractual | 69 PASS | 69 PASS | [JUnit Windows](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/windows/junit.xml), [Linux](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/linux/junit.xml) |
| Regresión T02 recetas | 183 PASS | 183 PASS | mismos JUnit, IDs individuales |
| Regresión T03 composición | 91 PASS | 91 PASS | mismos JUnit, IDs individuales |
| Generador privado | 3 PASS | 3 PASS | [Windows](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/windows/private.junit.xml), [Linux](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/linux/private.junit.xml) |
| Code-first en memoria | byteexact | byteexact | [Windows](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/windows/codefirst.json), [Linux](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/linux/codefirst.json) |

La regeneración usa DTOs nativos en modo serialization y descriptor cerrado: 310 nodos, nueve nodos modificados, 11 traducciones locales. Metaschema Draft2020-12 y pares positivos/negativos verifican cardinalidad de arrays y límites numéricos. El schema limita forma/localidad; business rules, hashes, autoridad y capacidades siguen exigidos por el codec. Los tres tests/generador privados se copiaron con normalización de newline declarada; sus AST coinciden con originales y [pins observados](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/private-observed-pins.json) conservan ambos SHA, sin atribuir un SHA original a la copia. No se ejecutó __main__ ni --check con escritura de audit sobre FIX1.

Runtime cambiado: cero. Cobertura de runtime modificado y TDD de producto: n/a; no se inventa un porcentaje por pruebas de configuración. Los 18 RED/2 controles de FIX1 son historia causal de restricciones, seguidos por 20 GREEN; **no son fallos actuales**. [Históricos autenticados](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/historical-preservation.json): 196 originales + 7 QA anterior + 238 FIX1 + 8 QA documental, todos byteexactos. La OpenAPI baseline f42 y sus dos exports/lint-diff0 corresponden al histórico ya revisado; no se reexporta ni se atribuye ejecución nueva. Los 22 JSON sintéticos conservan hashes, IDs/textos/pins ficticios y runtime_verified=false; no acreditan derechos reales de audio/modelos ni custodia.

[Baseline actual](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/snapshot/docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/contract-baseline.md) y [33 enlaces comprobados](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-current-qa1-20261011/baseline-links.json): resueltos desde destino canónico; fallback privado declarado para candidatos aún sin adoptar, con SHA actual exacto. Los enlaces de .cache son evidencia local ignorada por Git, no una promesa de disponibilidad pública. Review2 A/B sin gaps se conserva en [transferencia ROOT](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-review2-20261011/verdict-transfer-root.md); A01/B01/B02 corregidos, sin reabrir historia ni aceptar hitos.

## Gates oficiales

Se adapta el JUnit real a un resultado por nombre de caso, sin retries ni estadística inventada. Es pytest CPU; **no reporter Playwright ni E2E**. Los checks de prosa/enlaces/generación se reportan aparte del gate.

Windows, exit0:
```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 343,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

Linux, exit0:
```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 343,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

ledger-lint exit0 sobre snapshot, salida íntegra:
```text
⚠️  T-04: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-05: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-06: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-07: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-08: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-09: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-10: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-11: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-12: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-13: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-14: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-15: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-16: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-17: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-18: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-19: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-20: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-21: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-22: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-23: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-24: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-25: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-26: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-27: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-28: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-29: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-30: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
ledger-lint: 0 incoherencias · 27 avisos (tasks.md)
```

coverage-check exit0, validación de referencias/plan, no evidencia de ejecución E2E:
```json
{"applies": true, "defined": ["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "E2E-12", "M-01", "M-02", "M-03", "M-04", "M-05", "M-06", "M-07", "M-08"], "referenced": ["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "E2E-12", "M-01", "M-02", "M-03", "M-04", "M-05", "M-06", "M-07", "M-08"], "broken_refs": 0, "tasks_sin_cobertura": [], "tests_sin_referencia": [], "gwt_cubiertos": ["CA-02", "CA-03", "CA-04", "CA-05", "CA-06", "CA-07", "CA-08", "CA-09", "CA-10", "CA-11", "CA-12", "CA-13", "CA-14", "CA-15", "CA-16", "CA-17", "CA-18", "CA-20", "CA-22", "CA-25", "CA-26", "CA-27", "CA-28", "CA-30"], "gwt_sin_cubrir": [], "gwt_sin_id": 0, "test_plan_na": false, "marcador_no_canonico": null}
```

## Manuales y aceptación pendientes

- [ ] E2E-12 real del plan: compatibilidad integrada del producto, todavía no ejecutado por este harness.
- [ ] M-08: comprobación humana del alcance contractual y regresión real M1.
- [ ] Los restantes E2E/manuales del hito siguen sujetos al test-plan; este verde unitario CPU no los sustituye.
- [ ] ROOT debe verificar payloads/guards y decidir adopción/cierre T04; QA no ejecuta CAS, Git ni cierre de tareas.

Trazabilidad: T04 CA1 lectores PostPlan/recipe/manifiesto/song y rechazo incompatible → focal69; CA2 sintéticos/no autoridad → fixtures/readers; CA3 verificación/review/QA → receipts/gates/transferencia. El sello/manifest permiten verificar todos los payloads. Tokens/euros/horas IA reales: null, las UTC son reloj de evidencia. Escrituras finalizadas al entregar el sello.
