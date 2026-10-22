# QA CPU independiente — reloj T09

QA_CPU_PASS; 247 casos CPU en dos suites distintas.

Producto: {'total': 215, 'failed': 0, 'skipped': 0}; piloto privado: {'total': 32, 'failed': 0, 'skipped': 0}. No se suman los controles previos de revisión ni los RED/GREEN solapados.

Cobertura oficial ponderada de ocho módulos completos: 83.68283093053735%; mínimo 80%; exclusiones 0. [JSON original](product-coverage.json).

## Gate CPU mediante adaptador explícito

Los testcase de los dos JUnit originales se convierten a stats esperados/inesperados/skipped; no existen reintentos ni ejecución Playwright/E2E.

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 247,
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

## Puertas y custodia

Ledger-lint y coverage-check oficiales: véanse [argv, UTC y exits originales](execution.json), stdout/stderr y JUnit. M0 declara sin UI por diseño: exención documental, no cobertura E2E acreditada.

```
ℹ️  test-plan: n/a (sin UI) declarado en improvement-plan.md: iniciativa sin UI por diseño, la puerta de cobertura NO se ha ejecutado (no es «cobertura OK»)
ℹ️  se listan para la revisión 21 tarea(s) del ledger (la spec no aporta criterios rastreables) (T-00, T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10, T-11, T-12, T-13, T-14, T-15, T-16, T-17, T-18, T-19, T-20): la puerta no exigía cobertura de estos (solo la exige de los [GWT]), así que aquí no se exime nada — su evidencia es el campo `Verificación` de la tarea que los cierra en tasks.md
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19", "T-20"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}

```

Ruff/formato sobre los cuatro ficheros del delta clock-fix1: checks originales, sin modificación de producción.

Custodia antes/después: 191 protegidos, 66 fuentes y 12 documentos cotejados contra los sellos originales. T20: CARRY-FORWARD de QA previa 12 documentos/156 enlaces por checksums intactos; no se repite el scan. [Recibo](receipt.json).

## Límites y pendientes

- No GPU, Docker, WSL, Ollama, sensors, UI, network or installations
- No new classification of original captures or metadata
- CPU approval does not close T09, M0, matrix160 or artistic choice
- Root owns ledger, publication and state changes
- PDF absent: renderer dependencies unavailable; installation prohibited; MD/JSON/JUnit supplied for no-UI scope

Pendientes reales: preflight e integración GPU del reloj y observación, matriz160, evidencia musical/elección artística y verificación canónica de T09. No se cierran tareas ni estados.

Ledger: 0 incoherencias duras y 7 avisos de campo Changelog ausente, sin afectar este gate CPU. benchmark.py y benchmark_runner.py quedan individualmente por debajo de 80%; el umbral autorizado corresponde al total ponderado completo (1277/1526).
