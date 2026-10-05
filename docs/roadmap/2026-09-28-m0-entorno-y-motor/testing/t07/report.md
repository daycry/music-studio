# QA independiente T-07 — CLI y primera canción

2026-10-05 · rama `m0/t-07-cli-first-song` · base `main` (`11c1884`).

**Veredicto técnico: pasa.** Suite CPU completa: **243 passed, 5 skipped, 1 deselected**, exit 0. Cobertura del código de producción cambiado: **93,98 %**, mínimo 80 %, exit 0. La primera impresión musical del propietario es negativa; no se declara calidad musical aceptada. QA no modifica el ledger ni cierra T-07 o M0.

ℹ️ **sin UI por diseño (`test-plan: n/a (sin UI)`)**. `ledger-lint` exit 0: 0 incoherencias, siete avisos por Changelog ausente T-07–T-13. `coverage-check` exit 0 acepta la declaración sin UI: la puerta criterios↔E2E no se ejecuta; no es «cobertura OK». No hay Playwright, capturas, escenarios E2E/API/A11Y, `results.json` ni `qa-gate.py` ficticios. E2E: no aplica, sin porcentaje.

## Puertas de entrada

Recibos: [ledger-lint](raw/qa-ledger-lint.log), [coverage-check](raw/qa-coverage-check.log).

Salida JSON real de `coverage-check`:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": "el diff contra la base «merge-base main…HEAD (11c18849)» no aporta ningún fichero: solo se han mirado los cambios sin comitear"}
```

`eximidos` identifica tareas revisables, sin exigencia GWT; no convierte sus verificaciones en pruebas UI. La búsqueda de rutas UI está degradada porque HEAD coincide con la base: solo considera alcance declarado y cambios sin comitear. No acredita inspeccionar un diff con commits propios. Marcador canónico, sin rutas UI detectadas en ese alcance.

Se leyeron CONTINUE-HERE, constitución, memoria local del proyecto, plan, criterios T-07 y revisión final. `docs/knowledge/` contiene journals, sin gotchas disponibles. No se escribe memoria ni se promueve conocimiento.

## Suite CPU y cobertura oficial

Entorno cargado con `scripts/env.ps1`; Python gestionado 3.12.14, `uv run --no-sync --all-packages`. El [runner](raw/qa-cpu-runner.py) ejecuta pytest oficial, `--cov=. --cov-report=json`, `-m "not gpu"`, `CUDA_VISIBLE_DEVICES=''`, temporales/cobertura en `.cache/`. Directorios creados con mkdir normal, sin cambios de permisos globales.

Paths explícitos: `packages/weights/tests`, `packages/engine-contract/tests`, `packages/audio-post/tests`, `apps/engines/common/tests`, `apps/engines/mock/tests`, `tests`, `apps/engines/acestep/tests`. Incluye el adaptador que pytest.ini raíz omite por defecto.

Resultado: **243 pasan, cinco omisiones host, un GPU excluido**, seis avisos, 25,10 s. Omisiones: cuatro tests de `test_environment.py` exclusivos del contenedor y `test_install_patch_on_actual_upstream_without_models`, cuya fuente auditada vive en la imagen fijada. No se declaran ejecutados aquí. Avisos: cinco deprecaciones Starlette por timeout en TestClient y uno de cacheprovider por WinError 5; no ocultan fallos de tests.

Recibos: [pytest y exit](raw/qa-cpu-tests.log), [comando/entorno](raw/qa-cpu-command.json), [coverage.py anonimizado](raw/qa-coverage.json), [stdout del gate](raw/qa-coverage-gate.log), [exit](raw/qa-coverage-gate-exit.txt), [JSON](raw/qa-coverage-gate.json).

Comando sin modificar herramienta ni umbral:

```text
coverage-gate.py . --changed-only --base main --min 80 --json
  --runner "<workspace>/.venv/Scripts/python.exe docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t07/raw/qa-cpu-runner.py"
```

Salida JSON real:

```json
{
  "ok": true,
  "exit": 0,
  "stack": "pytest",
  "detalle": {
    "stack": "pytest",
    "informe": "coverage.json",
    "global": 27.54,
    "modo": "changed-only",
    "base": "main",
    "ficheros": {
      "scripts/generate.py": 93.98
    },
    "porcentaje": 93.98,
    "minimo": 80.0
  },
  "avisos": [
    "sin datos de cobertura para: docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t07/raw/qa-cpu-runner.py (excluidos de la media)"
  ]
}
```

Métrica: media por fichero cambiado, no cobertura de líneas del diff ni porcentaje global. Único fichero de producción cambiado: `scripts/generate.py`, 312/332 statements. El gate excluye automáticamente el runner QA sin datos, como declara el JSON; no hay exclusión manual. El 27,54 % global incluye archivos fuera del alcance ejecutado y no determina el veredicto.

La primera invocación con barras Windows en `--runner` falló antes de pytest con WinError 2 por el parseo shlex. El gate leyó cobertura preexistente y devolvió exit 0 con `ficheros: {}`: **esa salida no acredita QA**. Se conserva el [recibo de invocación fallida](raw/qa-coverage-gate-invocation-failed.log). Se corrigió solo la sintaxis del comando a barras `/`; la segunda invocación ejecutó pytest real y regeneró cobertura. No se repitió suite fuera del gate.

## Verificaciones adicionales

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Ruff global | exit 0, All checks passed | [log](raw/qa-ruff.log) |
| Formato generate.py, test_generate.py y runner QA | exit 0, 3 files already formatted | [log](raw/qa-format.log) |
| Contratos, --check | exit 0, engine-v1.json up to date | [log](raw/qa-contracts.log) |
| verify_manifest.py data/cli/ | exit 0, all valid (2 manifests) | [log](raw/qa-manifests.log) |
| git diff --check | exit 0; avisos CRLF→LF de documentos existentes | [log](raw/qa-diff-check.log) |

Sin lectura/copia de letra, estilo, token o contenido de manifiestos privados. Rutas personales anonimizadas. Sin cambios a producto, dependencias, datos, modelos, estados o Git.

## Trazabilidad T-07

| Criterio | Resultado y evidencia |
|---|---|
| CLI directa/catálogo, opciones y autenticación | suite CPU e integración mock/FFmpeg; [pytest](raw/qa-cpu-tests.log), [revisión A+B+D sin gaps](review-attempt3.md) |
| Eventos, cuatro archivos, procedencia/publicación inmutable | suite CPU y [revisión](review-attempt3.md) |
| Ctrl+C, error primario, cleanup único ≤300 s y trabajo ajeno | regresiones CPU verdes, [pytest](raw/qa-cpu-tests.log), [revisión](review-attempt3.md) |
| Primera toma recuperada del CLI exit 1 | [recibo existente](first-song-technical-receipt.json); no acredita CLI original exit 0 |
| CLI completo sin instrumentación, nueva toma 255 s, exit 0 | [recibo existente](cli-full-generation-receipt.json); ambas tomas preservadas, dos manifiestos válidos en QA |
| Helper corregido contra contrato real de job completado | [HTTP GET exclusivamente](cleanup-live-contract-receipt.json), idle/loaded=null; sin cancelación GPU real |
| Autoría y primera impresión | own recibida; escucha negativa recibida, checklist siguiente |

No se repite generación, build ni GPU por fixes de error. Recibos de generación acreditan su código/momento originales; fixes posteriores de cleanup se acreditan con regresiones CPU y comprobación HTTP de solo lectura. Tests no acreditan alineación de voz/acompañamiento, calidad musical, cancelación GPU real ni capacidades de producto pendientes de T-10.

## Checklist manual

Sin test-plan.md ni IDs M-xx por diseño sin UI; lista derivada de criterios manuales T-07.

- [x] Declaración explícita `own` recibida previamente del propietario.
- [x] Primera toma escuchada, job `01M465ZQTFYQK9ATZNG2X63KYJ`; impresión: «la voz y la música parece que no van acorde».
- [x] Aclaración posterior recibida: ritmo/encaje, afinación y carácter de voz; calidad musical no aceptada. [Respuesta](owner-quality-details.json).
- [ ] Valorar segunda toma si el propietario lo decide; no se presume que la impresión corresponda a ambas.

La selección/evaluación de calidad pertenece a T-13. La impresión negativa no cambia el resultado CPU ni constituye un defecto técnico reproducido. El orquestador mantiene estados y respuesta humana; no hay cierre de M0 ni handoff a documenter/curator por este agente.

## PDF y entrega

Markdown generado; PDF pendiente. Node existe, pero faltan dependencias de `custom-agents:to-pdf` en la caché local comprobada y en la caché de usuario de esa skill. [Recibo](raw/qa-pdf-tooling.json). El encargo prohíbe instalar y autoriza declarar la limitación; no se instala ni se pausa por PDF. Jira/Confluence desactivados; informe local.

## Actualización del orquestador tras QA

El propietario entregó su corpus de Suno como referencia y concretó los tres desajustes. [Diagnóstico inicial con evidencia y límites](prompt-model-diagnosis.md). No se repiten ni alteran los resultados técnicos de QA.

Al preparar Git, `diff --cached --check` detectó espacios al final de líneas en tres logs nuevos de PowerShell, que el check anterior de cambios tracked no incluía. Se retiraron únicamente esos espacios en las copias públicas; texto, errores y resultados se conservan. No hubo cambio de producto ni repetición de tests.
