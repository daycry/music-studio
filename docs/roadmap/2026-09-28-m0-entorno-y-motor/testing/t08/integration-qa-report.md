# T-08 — QA independiente del delta de integración CLAP

2026-10-06. **Conforme en el alcance CPU; T-08 continúa en-progreso.** Esta auditoría verifica la entrega posterior a revisión A+B+C de integración1, sin cerrar sus tres criterios de aceptación, ASR, score CLAP GPU ni M0. No acredita calidad musical.

## Resultado y trazabilidad

| Comprobación nueva | Resultado | Evidencia |
|---|---|---|
| Suite CPU de fuentes propias de la imagen final | 47 passed, 0 failed, 0 skipped, 4 GPU deselected; exit 0; 27,52 s | [Log](../../../../../.cache/dev-cycle/t08/integration-qa/suite.log), [JUnit](../../../../../.cache/dev-cycle/t08/integration-qa/results.xml) |
| Cobertura oficial pytest-cov | 346/382 = 90,5759 %; backend cambiado 185/208 = 88,9423 %; ambos ≥80 % | [JSON](../../../../../.cache/dev-cycle/t08/integration-qa/coverage.json) |
| Regresión del prefijo real local | Casos 1 s y 30 s incluidos en los 47, procesador/tokenizer reales, resample 24→48 kHz, BN BF16/reshape/Conv2d real; [1,1,1001,64], tokens íntegros y ventana 10 s | JUnit, test_clap_prefix.py; llamada backend:343 ejecutada, keyword:348 no es sentencia independiente |
| Integridad | 21 fuentes y 14 artefactos históricos coinciden antes/después; 18 fuentes de imagen coinciden | [Recibo](integration-qa-receipt.json), [probe](../../../../../.cache/dev-cycle/t08/integration-qa/image-probe.json) |
| Imagen y usuario | 7d0733f939606e14dda786941e505f3c23e9565272c4d1fd8a83dbc12efc279d; User=engine | [Imagen](../../../../../.cache/dev-cycle/t08/integration-qa/image-id.log) |
| Imagen original conservada | 306e3b0fbc1170ee066e2aed099ef6638ea7dad7faf3ab5b67edfa90e64b70c9 intacta | [ID original](../../../../../.cache/dev-cycle/t08/integration-qa/original-image-id.log) |
| Ruff / formato | exit 0 / 16 files already formatted | [Ruff](../../../../../.cache/dev-cycle/t08/integration-qa/ruff.log), [Formato](../../../../../.cache/dev-cycle/t08/integration-qa/format.log) |
| Compose filtrado sin secretos | tag m0-t08-clap-integration, puerto 127.0.0.1:8130, mount /models RO, config exit 0 | [Metadata](../../../../../.cache/dev-cycle/t08/integration-qa/compose-metadata.json) |
| Ledger | 0 incoherencias, 7 avisos Changelog; exit 0 | [Log](../../../../../.cache/dev-cycle/t08/integration-qa/ledger-lint.log) |

Un aviso de Starlette/anyio deprecado, sin fallo. Los 45 tests de la QA anterior siguen siendo evidencia histórica; esta ejecución nueva mide 47 y no altera los anteriores. Delta auditado: una línea productiva de estrategia CLAP, test de prefijo real nuevo, README y tag Compose. El proceso padre gestionado no dispone de torch.

## Entorno y límites

Contenedores CPU efímeros por SHA, `--network none`, CUDA_VISIBLE_DEVICES vacío, NVIDIA_VISIBLE_DEVICES=none, sin `--gpus`; recursos locales /models:ro, escrituras solo en carpeta nueva de evidencias. Probe: siete recursos JSON/TXT del modelo hashados, CUDA no inicializada; sin carga de pesos CLAP. No build, descarga, inferencia GPU, suite global, modificación de código, Compose, ledger, Git, conocimiento o fuentes concurrentes T-16. Constitución §2/§4 respetada: runtime local, pesos seguros, sin exposición de puertos adicionales. El aislamiento de red es del contenedor de prueba, no modifica la red del servicio.

La prueba sustituye el cálculo posterior a la proyección real por embeddings dobles. Su resultado no demuestra embeddings completos, score real, exactitud ASR, descarga/residencia GPU ni obediencia artística. Los casos sintéticos son duraciones 1/30 s; no hay semillas musicales ni audio generado. Revisión A+B+C integración1 sin gaps y RED/GREEN de implementer son antecedentes conservados, no ejecuciones propias de QA.

## Sin UI por diseño

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`). coverage-check exit 0, applies=false: la puerta E2E de cobertura **no se ha ejecutado**. No test-plan E2E/M/API/A11Y, ni Playwright, capturas o results.json ficticios. **qa-gate: n/a**, no existe JSON de gate que pegar para este tramo sin UI; la conformidad CPU viene de pytest/cobertura y no equivale al verde E2E.

Salida determinista coverage-check:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

Estos 20 IDs se listan para revisión, sin exigencia de cobertura [GWT]; su Verificación es la evidencia canónica. No degradación de diff ni aviso de UI esta vez. [Salida completa](../../../../../.cache/dev-cycle/t08/integration-qa/coverage-check.log).

PDF pendiente: Node v22.23.2 existe; dependencias to-pdf ausentes en caché canónica y local. Se consultó `custom-agents:to-pdf`; no se instaló nada ni se generó un PDF ficticio, conforme al scope autorizado. [Disponibilidad](../../../../../.cache/dev-cycle/t08/integration-qa/pdf-availability.json). No handoff documenter ni cierre de plan/spec por QA parcial. Medición agregada del orquestador: lote integration-clap-sft-diagnosis; tokens/coste/horas reales desconocidos, sin atribución individual.

## Pendientes de validación

- [ ] Orquestador: score CLAP completo en GPU, preflight nuevo y aislamiento autorizados.
- [ ] ASR real y su diagnóstico siguen pendientes.
- [ ] Verificar el resto de CA T-08 con sus evidencias: tareas reales, residencia/descarga y pruebas declaradas; no cerrar por este delta.
- [ ] Escucha humana y aceptación artística continúan pendientes; no hay ganador/modelo elegido por QA.
- [ ] PDF, cuando exista el entorno autorizado para convertirlo.
