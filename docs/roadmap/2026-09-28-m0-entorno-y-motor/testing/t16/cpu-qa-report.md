# Informe de QA — T-16, tramo CPU independiente

| | |
|---|---|
| Fecha | 2026-10-06 |
| Estado | **QA CPU conforme; T-16 y M0 abiertos** |
| Plan | [Plan](../../improvement-plan.md) · [Ledger](../../tasks.md) |
| URL / UI | Sin URL auditada; sin UI por diseño (`test-plan: n/a (sin UI)`) |
| Recibo | [cpu-qa-receipt.json](cpu-qa-receipt.json) |

## Veredicto y puertas

`qa-gate.py` E2E **n/a** por la excepción canónica sin UI: no se ejecuta Playwright ni se fabrica results.json. No existe porcentaje E2E. El veredicto conforme se limita a las comprobaciones CPU detalladas abajo; no cierra la tarea, plan, spec ni hito, y no activa handoff de cierre.

Ledger-lint ejecutado: **0 incoherencias, 7 avisos** (Changelog ausente en T-08–T-13 y T-16).
Salida JSON real de coverage-check, copiada sin modificación:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": "el diff contra la base «merge-base main…HEAD (ef66a36b)» no aporta ningún fichero: solo se han mirado los cambios sin comitear"}
```

La puerta de cobertura UI **no se ha ejecutado**; la declaración no equivale a cobertura acreditada. Los veinte IDs se listan para revisión, `eximidos_exigidos=false`. La comprobación de rutas UI no miró un diff completo con commits propios: la base merge-base coincide con HEAD y solo se inspeccionaron cambios sin comitear más alcance del ledger. No detectó rutas UI en ese alcance. Marcador canónico, sin referencias rotas evaluadas ni bloques E2E/M/API/A11Y definidos.

## Pruebas CPU nuevas

Entorno cargado con `scripts/env.ps1`; Python gestionado 3.12.14 y `uv run --frozen --all-packages`. Logs y JSON oficiales propios en `.cache/dev-cycle/t16/qa/`; no dependencias instaladas.

| Comprobación | Resultado nuevo | Evidencia privada |
|---|---|---|
| Verificación declarada T-16, dos archivos | **41 passed**, exit 0 | `declared.txt` |
| Workspace explícito `tests packages apps/engines`, sin GPU | **430 passed, 5 skipped, 1 deselected, 6 warnings**, exit 0 | `full.txt`, `coverage.json` |
| Exportador de contratos `--check` | engine-v1.json up to date | `contracts.txt` |
| Manifiestos de ejemplos / CLI privados | **4 / 14 válidos** | `examples.txt`, `cli-manifests.txt` |
| Ruff global / formato del alcance | All checks passed / **10 files already formatted** | `ruff.txt`, `format.txt` |
| Diff-check | Sin errores de espacios; avisos CRLF de CONTINUE-HERE/tasks | `diff-check.txt` |
| Imagen inspect | Digest coincide con recibos nativo/HTTP | `image.txt` |

Cinco avisos son deprecación Starlette/TestClient; el sexto es PytestCacheWarning/WinError5 al crear la caché de nodeids propia. No falló ninguna prueba y el JSON oficial de cobertura se generó. Los skips/deselected no se presentan como pruebas ejecutadas. Algunas fixtures históricas usan temporales propios bajo `.cache/dev-cycle/t03`; no se limpian datos ajenos.

Formato comprobado de seis producciones y `test_preflight.py`, `test_inference_controls.py`, `test_generate_inference.py`, `test_generate_preparation.py`. El recibo recoge comandos exactos de pytest y cruces independientes; los hashes SHA256 de las seis producciones congelan el alcance QA.

## Cobertura unitaria nueva del cambio

Medida oficial nueva por directorios, no rutas de archivo. Cruce propio de statements ejecutables añadidos con `git diff ef66a36bedf08fb996f88ef6cb9633b5f51f13b8 --unified=0`: **59/63 = 93,65 %**, mínimo por archivo medible **86,36 %**, ambos ≥80 %. Los cuatro statements añadidos no cubiertos figuran en el recibo. No se reutiliza la cobertura del implementer.

| Producción | Statements añadidos cubiertos | Cobertura añadida | Archivo completo |
|---|---|---|---|
| `apps/engines/acestep/adapter.py` | 12/13 | 92.31 % | 92.58 % |
| `apps/engines/acestep/descriptor.py` | 4/4 | 100.00 % | 100.00 % |
| `apps/engines/acestep/input_profile.py` | 7/7 | 100.00 % | 100.00 % |
| `apps/engines/acestep/preflight.py` | 2/2 | 100.00 % | 90.48 % |
| `packages/audio-post/audio_post/manifest.py` | 19/22 | 86.36 % | 92.38 % |
| `scripts/generate.py` | 15/15 | 100.00 % | 93.88 % |

## Recibos, entradas e integridad

Probe independiente nuevo: **13 records** nativos válidos, mismo SHA256 antes/después (`1624b5e8824e82faa521746b0549f602a759827313ff8ddd3aa8efa839c2e753`). Rechaza **7** contradicciones rehasheadas: checkpoint, identidad, pasos/CFG en flags, booleanos en pasos/CFG efectivos y booleano en solicitud. Baseline preservado. Los pares `libre_t15_control`/`control_sft50` tienen `planned.lm`, `planned.dit` y `effective.lm_metadata` idénticos, controles8/50.

Las pruebas nuevas ejecutadas incluyen `test_native_sft_effective_receipt`, `test_dit_boundary_rejects_inference_drift` y progreso/cancelación. La frontera real registra hash de kwargs; el validador y la suite prueban controles y rechazo de deriva, sin reconstruir cada kwargs privado de todos los captures. El recibo nativo existente acredita orquestación/tokenizadores CPU reales con forward sustituido: no inferencia ni audio. Turbo recibe CFG7 en la entrada y su handler interno fuerza1; no se atribuye CFG7 a su sampler.

Se comprobaron por lectura **32 hashes históricos** del inventario T-17 (originales/corpus/control), **72 versos/nueve tags** y **16 hashes de tokenizer**. Alcance delimitado: no auditoría de todos los privados, takes o bytes de cada audio. No se reescriben corpus, configuraciones, preparaciones ni recibos originales.

## Antecedentes independientes del resultado nuevo

[Revisión1 A+B](review-1.md) fresca sin gaps; selector C/D=false. TDD/RED del [implementer](cpu-implementation-report.md) es antecedente, no reproducción RED QA.

[Integración CPU](cpu-integration-report.md): imagen `sha256:9e4fc86fe17269ef80ad6649d9f80b02f8d1f0c7af160f3f9d0fde362dfd8f84` inspeccionada ahora. Sus **156 passed/1 deselected/5 warnings** son ejecución previa leída, no nueva QA; no build ni probe repetidos. [Recibo HTTP](http-controls-receipt.json) y logs de dos contenedores efímeros CPU leídos: CpuGpu **sintético**, sin NVML ni telemetría GPU propia, sin jobs válidos. No se tocó el servicio8101 anterior ni Ollama.

## Documentación y privacidad

Revisión automática delimitada de **17 documentos** públicos tocados y Markdown/JSON T-16: **237 enlaces a archivos locales** existentes; no se comprobaron anchors. Sin parámetros privados completos de las trece solicitudes (letras/style/negative_prompt), rutas personales Windows ni patrones de token detectados. No es revisión exhaustiva de fragmentos ni escaneo general de secretos. Lista de archivos/método en el recibo; journals excluidos sin lectura ni promoción.

## Trazabilidad y checklist pendiente

| Criterio T-16 | Resultado |
|---|---|
| CA1 identidad/defaults/límites/CLI/progreso | CPU conforme por las 41 pruebas declaradas y vecinas |
| CA2 TDD/revisión/QA/cobertura/documentación | Tramo CPU conforme; TDD y revisión como antecedentes |
| CA3 seis tomas/metadata/telemetría/unload | **Pendiente**, CPU no acredita ejecución GPU |
| CA4 pares ciegos/nivel/escucha humana | **Pendiente**, sin ganador ni calidad aprobada |

- [ ] Ejecutar seis tomas emparejadas nuevas con guardas GPU/Ollama/VRAM actuales, identidad y controles efectivos.
- [ ] Verificar telemetría real, cap dinámico, ausencia de spill y unload de cada generación.
- [ ] Construir/verificar escucha privada y valorar ritmo, afinación, voz e instrumentos; preservar referencias y takes.
- [ ] PDF pendiente: dependencias del renderer no disponibles en las rutas comprobadas; no instalar y no escribir salidas fuera del ownership asignado.

No carga de modelos, GPU, generaciones, instalaciones ni jobs válidos en esta QA. No cambios en ledger, Git ni marcadores de consumo. M0/T-08–T-13 y objetivo musical siguen abiertos; no aprobación artística ni cambio de motor por defecto.
