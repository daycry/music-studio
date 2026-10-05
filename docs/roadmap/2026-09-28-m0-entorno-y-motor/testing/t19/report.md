# Informe de QA — T-19, preflight nativo y entradas efectivas

| | |
|---|---|
| Fecha | 2026-10-06 |
| Estado técnico | **CONFORME CPU, sin UI por diseño**; 0 fallos reproducidos |
| URL de lectura | `http://127.0.0.1:8101/v1/health`, solo local |
| Plan | [Plan M0](../../improvement-plan.md) · [Ledger](../../tasks.md) |
| Evidencia reproducible | [Recibo QA independiente](qa-receipt.json); logs y JSON completos en `.cache/dev-cycle/t19/qa/` |

## Veredicto y puertas

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`). `qa-gate.py` de Playwright **no aplica y no se ha ejecutado**. No existen resultados E2E, capturas UI ni porcentajes E2E fabricados. El resultado conforme corresponde a la verificación backend CPU; no cierra M0 ni cambia spec/plan/ledger.

Salida real de `ledger-lint.py`:

```text
⚠️  T-08: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-09: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-10: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-11: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-12: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-13: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-16: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-19: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
ledger-lint: 0 incoherencias · 8 avisos (tasks.md)
```

Salida JSON real de `coverage-check.py`, exit 0:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": "el diff contra la base «merge-base main…HEAD (83fc652c)» no aporta ningún fichero: solo se han mirado los cambios sin comitear"}
```

La puerta de cobertura E2E no se ha ejecutado: el marcador canónico declara la exención. `eximidos_exigidos=false`: los veinte IDs listados se proporcionan para revisión del ledger; no son criterios GWT dispensados. No hay rutas UI detectadas, pero la comprobación está degradada porque el merge-base no aporta commits propios: solo alcance declarado y cambios sin comitear. No se presenta ese resultado como cobertura UI comprobada.

## Pruebas actuales independientes

| Comprobación | Resultado y evidencia privada local |
|---|---|
| Cinco módulos de Verificación T-19 | **146 passed, 1 skipped**, exit 0; `declared.txt` |
| Workspace explícito `tests packages apps/engines`, con coverage.py oficial | **381 passed, 5 skipped, 1 deselected, 5 warnings**, exit 0, 22,92 s; `full-coverage.txt` |
| Exportador code-first | `engine-v1.json up to date`, exit 0; `contracts.txt` |
| Manifiestos de ejemplo | `all valid (4 manifests)`, exit 0; `examples.txt` |
| Manifiestos privados CLI existentes | `all valid (14 manifests)`, exit 0; `manifests.txt`; lectura, sin regeneración |
| Ruff global | `All checks passed!`, exit 0; `ruff.txt` |
| Formato Python de T-19 | 15 ficheros ya formateados, exit 0; `format.txt`; no se exige formato histórico fuera del alcance |
| `git diff --check` | exit 0; `diff-check.txt` conserva avisos CRLF de Git |
| Guardrail local/privado | `guardrail_assert` sobre health local, exit 0; `guardrail.txt` |
| CLI ayuda | exit 0; `help.txt`; prepare-only y publicación se verifican en tests actuales con material sintético |
| Lectura recibos, corpus e identidad | `existing.json`, todas las aserciones conformes |
| Privacidad y enlaces | 38 ficheros, 252 enlaces locales y 11 anchors, cero hallazgos; `public-scan.json`, `anchors.json` |

Las cinco advertencias son `StarletteDeprecationWarning` por `timeout` en TestClient, en cinco tests de generate; no se silencian. Cuatro skips corresponden al entorno real exclusivo de imagen, otro a patch de upstream exclusivo de imagen. El test GPU queda excluido por `not gpu`. No se ejecuta ninguna GPU. Fixtures existentes usan también `.cache/dev-cycle/t03` en lugar de respetar siempre basetemp; se conserva ese contenido. No se instalan herramientas ni dependencias. Los scripts QA de lectura corrigieron una decodificación cp1252 inicial usando UTF-8; no fue fallo de producto.

## Cobertura independiente del cambio

**350/377 statements añadidos = 92,84 %**, mínimo por archivo medible **87,50 %**, umbral 80 %. Datos nuevos oficiales de coverage.py (`coverage.json`), sin mezclar coberturas históricas. `measure.py` cruza statements ejecutados/faltantes con líneas añadidas contra `83fc652`; incluye todos los statements de los dos módulos nuevos. El descriptor cambia literales sin statements nuevos y se mide completo, fuera del denominador agregado. Sources por directorio evitan imports anticipados de NumPy/torch. No se atribuye este porcentaje a E2E ni a calidad musical.

| Archivo | Statements cubiertos/medidos | Cobertura | Método |
|---|---|---|---|
| `apps/engines/acestep/preflight.py` | 133/147 | 90.48 % | statements del cambio |
| `apps/engines/acestep/input_profile.py` | 7/7 | 100.00 % | statements del cambio |
| `apps/engines/acestep/adapter.py` | 100/102 | 98.04 % | statements del cambio |
| `apps/engines/acestep/descriptor.py` | 30/30 | 100.00 % | fichero completo: literal sin statements añadidos |
| `apps/engines/acestep/engine_acestep.py` | 1/1 | 100.00 % | statements del cambio |
| `apps/engines/common/engine_common/server.py` | 7/8 | 87.50 % | statements del cambio |
| `scripts/generate.py` | 38/43 | 88.37 % | statements del cambio |
| `packages/audio-post/audio_post/manifest.py` | 64/69 | 92.75 % | statements del cambio |

## Trazabilidad T-19 → CA1–CA7

| Criterio | Resultado y evidencia |
|---|---|
| CA1: presupuesto nativo completo | Conforme: tests actuales de límites LM/DiT; recibos conditional/unconditional y reserva integral contrastados. Dieciséis hashes locales de tokenizadores y hash del script del probe comprobados hoy. |
| CA2: rechazo previo y fallo cerrado | Conforme: módulos actuales preflight/common/adapter; pruebas sin carga ni aceptación de jobs. Se conserva antecedente HTTP de ocho checks, no se repite. |
| CA3: caption largo y compatibilidad | Conforme: tests de caption, instrumental, seeds, shift y fixtures históricas incluidos en suite explícita. |
| CA4: idioma/metadata sin reescritura | Conforme: regresiones semánticas actuales, alias/omisión/instrumental y validación de capturas. |
| CA5: recibos privados verificables | Conforme: diez payloads nativos aceptados por producción actual, bytes antes/después intactos; baseline original de review-B aceptado, contradicciones idioma/shift/CoT originales rechazadas con `INPUT_RECEIPT_INVALID`. Padre de ese probe sin torch/transformers. |
| CA6: diferencial y límites artísticos | Conforme técnico: corpus anterior 16 casos/10 aceptados/6 rechazados conservado; 32 hashes de originales vigentes, preparación privada existente válida y 72 versos/9 tags íntegros. No se vuelve a preparar corpus ni a ejecutar probe T-17/T-18. Obediencia musical pendiente. |
| CA7: TDD, revisión y puertas | Conforme CPU: evidencia RED y [fix1](fix1-report.md) leídos, [revisión A+B+C intento 2](review-2.md) sin gaps; suites/cobertura/contratos/lint actuales conformes. No dependencias, pesos ni instalaciones nuevos. |

## Integración anterior y lectura actual

[Integración CPU/HTTP](integration-report.md), [recibo nativo](native-integrated-receipt.json) y [recibo HTTP](http-receipt.json) son evidencia **anterior**, no ejecución nueva de QA: 133 tests CPU de imagen, 16 casos de probe con diez aceptados y seis rechazados, ocho comprobaciones HTTP. Se leyó también la corrección [review-1](review-1.md), [fix1](fix1-report.md) y [review-2](review-2.md).

Hoy `docker image inspect` y health solo lectura coinciden en `sha256:13326c0f3aab17230ab05ec88d0ddecd414740f02900cc76caf47b965bb07801`; health indica idle, loaded=null, job_id=null. Hash del script del probe integrado coincide con el recibo. La corrección posterior afecta host audio-post y tests, no producción engine; no exige nuevo build ni repetir forward. Las capturas anteriores ejecutan orquestación/tokenización real CPU con forward sustituido; **no son audio real ni carga de modelo musical**. No se envía ningún POST ni job aceptable en QA.

Los 32 hashes preservados, diez payloads integrados y preparación CAS anterior se comprobaron en lectura sin modificar originales, corpus, privados ni journals. La comprobación pública busca versos largos exactos, secretos reales de entorno y rutas absolutas personales; cero hallazgos dentro del alcance examinado, no una garantía universal. No se navegan enlaces externos. Sin gotchas coincidentes y sin flakiness observado; no se escribe conocimiento.

## Checklist manual pendiente

- [ ] Obediencia musical de instrucciones y tags: escuchar y evaluar según [rúbrica canónica](../../../../calidad/evaluacion-escucha.md), T-08/T-12/T-13.
- [ ] Naturalidad de voz, afinación, ritmo e instrumentos y selección por escucha: pendiente; tokens transportados no aprueban estas dimensiones.
- [ ] Generación GPU/audio posterior: fuera de esta auditoría CPU; requiere el flujo y autorización aplicables.
- [ ] UI/E2E cuando exista UI: no corresponde a M0 sin UI por diseño.
- [ ] PDF: pendiente; las dependencias existentes de `to-pdf` no están disponibles, no se instalan por instrucción del brief.

## Estado y handoff

T-19 conforme técnicamente para decisión del orquestador; QA no modifica el ledger, Git ni marcadores. M0 sigue abierto, sin documenter ni ritual de cierre del hito. Medición IA real desconocida: tokens, horas y coste null; el tiempo de reloj no equivale a consumo IA. Recibo con hashes de producción actual conserva la identidad auditada.
