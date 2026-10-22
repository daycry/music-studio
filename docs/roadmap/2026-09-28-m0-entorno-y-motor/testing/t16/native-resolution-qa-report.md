# T-16 — QA independiente de resolución nativa, solo CPU

2026-10-06. **DONE_WITH_CONCERNS**: comprobaciones CPU conformes; no autoriza cerrar T-16/M0 ni declarar calidad o viabilidad GPU. Revisión A+B+C fresca previa sin gaps en `native-resolution-review-1.md`. Propiedad de este despacho: únicamente `.cache/dev-cycle/t16/native-resolution-qa/`.

## Evidencia ejecutada

Entorno `. ./scripts/env.ps1`, Python gestionado 3.12.14, `uv run --no-sync --all-packages`. Sin instalación, descarga, GPU, modelos completos, torch host o mutaciones Git.

Suite final independiente:

```text
pytest apps/engines/acestep/tests packages/audio-post/tests tests/test_generate_preparation.py tests/test_generate_inference.py -m 'not gpu' --cov=apps/engines/acestep --cov=packages/audio-post/audio_post --cov-report=json:.cache/dev-cycle/t16/native-resolution-qa/coverage.json --cov-report=term --junitxml=.cache/dev-cycle/t16/native-resolution-qa/junit.xml --basetemp=.cache/dev-cycle/t16/native-resolution-qa/tmp-final -o cache_dir=.cache/dev-cycle/t16/native-resolution-qa/pytest-cache -q
314 passed, 5 skipped, 1 deselected in 8.21s
```

Cero warnings en esta ejecución. Las **41 pruebas declaradas** de `test_generate_inference` y `test_inference_controls` están contenidas en esta misma suite, identificadas individualmente en JUnit y todas pasan; no se suman ni se repiten por separado. No se ejecutó la colección global 326 del workspace. Cobertura oficial pytest-cov nueva, sin append y con `COVERAGE_FILE` propio. El total de módulos/tests mostrado por pytest-cov no es el porcentaje del cambio ni un gate global.

Omitidas: `test_install_patch_on_actual_upstream_without_models`, `test_startup_log`, `test_runtime_dependencies`, `test_ffmpeg_shared_lgpl`, `test_runtime_configuration`. Son condiciones de upstream/entorno de contenedor ausentes en el host; no se consideran ejecutadas. Una prueba GPU queda excluida por `-m 'not gpu'`. No repetí la suite CPU158 del contenedor: existe evidencia sellada y no es necesaria para repetir el delta validado; el probe de fuentes/import del contenedor sí se ejecutó de nuevo.

## Cobertura independiente del cambio

`verify.py` obtiene cada baseline mediante **git show 8663287:ruta**, compara su SHA con el baseline declarado y calcula líneas nuevas/modificadas mediante difflib. Interseca las líneas con `executed_lines`/`missing_lines` del JSON oficial fresco. Git fue exclusivamente lectura.

| Fuente | Cubiertas/cambiadas ejecutables | % cambiado | % fichero completo |
|---|---:|---:|---:|
| adapter.py | 27/28 | 96,43 % | 92,90 % |
| preflight.py | 12/13 | 92,31 % | 90,63 % |
| input_profile.py | 0/0 | n/a | 100 % |
| manifest.py | 25/27 | 92,59 % | 92,37 % |

**64/68 = 94,12 %**, mínimo por fichero cambiado **92,31 %**, umbral 80 % conforme. Líneas cambiadas no cubiertas: adapter237, preflight417, manifest236/258. El agregado es ponderado por statements y no mezcla cobertura de anteriores suites. `input_profile.py` modifica metadata de un dict existente y no aporta statements nuevos; no se inventa un 100 % cambiado.

## Congelación y fronteras verificadas

Los **9 SHA de fuentes y 64 SHA de artefactos** del recibo de entrega coinciden antes y después de la suite final y tras los probes. Los bytes privados solo se hashean para el inventario autorizado: no se interpretan ni se muestran letras/códigos/trazas. La primera ejecución ocurrió antes de guardar el checkpoint previo; se repitió una única vez la misma suite acotada para reparar esa ausencia y disponer de antes/después verificables. No se alteraron fuentes ni evidencia entregada.

Imagen inspeccionada en vivo por tag: `sha256:18d94fd4b377016a895e5cd89ee446b64c872421b0d401987f58b0583b16da2d`. Probe independiente por ID, `docker run --rm --network none -e CUDA_VISIBLE_DEVICES= --entrypoint python`, sin `--gpus` ni mounts de modelos/inputs: **seis SHA de fuentes iguales al host/recibo**, importación de `engine_acestep` con `torch` ausente de `sys.modules`. Sin igualdad del Compose completo: el cambio ajeno de analysis está expresamente fuera de este alcance.

La suite fresca cubre resolver nativo fijado por ocho SHA, dos presupuestos al borde/+1, candidatos v2, instrucciones inicial/efectiva, binding de token IDs, summary HTTP real TestClient, publicación privada CAS del CLI, contradicciones rehasheadas, worker v2 y lectura histórica v1. Los tests de resolución/preflight usan dobles cuando está declarado; no son medición de inferencia/tokenizadores reales.

Leídos únicamente `integrated-native-public.json`, `integrated-original-public.json` y `validation-receipt.json`, sanitizados y sellados. Acreditan **8 recibos CPU publicados + 8 incompatibilidades rehasheadas rechazadas**, **13 v1**, **32 archivos históricos** y **27 evidencias diagnósticas** preservadas. Este despacho verifica hashes y coherencia de esos contadores; no reejecuta las integraciones privadas ni certifica su contenido por inspección. Sus forwards LM/DiT están doblados; no equivalen a inferencia real. La correspondencia histórica LM y preservación de originales procede de esos recibos sellados.

## Puertas y límites

`coverage-check applies=false`; `qa-gate=n/a` para este despacho CPU sin UI. No existe un veredicto Playwright ni se fabrica JSON de qa-gate, PDF o screenshots. Puertas del ledger/plan y publicación final pertenecen al orquestador; este agente no los modifica. Constitución respetada: trabajo local dentro del repo, sin persistencia de engine/BD, sin cargas de pesos ni GPU y sin datos publicados.

- [ ] CA2 reabierta: root incorpora y valora esta QA del alcance CPU.
- [ ] CA3/CA4: inferencia GPU 30 s, seis tomas 90 s y escucha/calidad pendientes.
- [ ] Harness GPU nuevo con cuatro cambios literales de configuración pendiente de su propia revisión/QA; no ejecutado aquí.

Únicamente procede el siguiente gate/preflight de root. No cerrar T-16/M0 ni aprobar GPU/calidad. No se tocó docs/knowledge, producto, documentación, ledger, Git, journals ni cachés ajenas. Evidencias propias: [receipt.json](receipt.json), [verification.txt](verification.txt), [pytest.txt](pytest.txt), [junit.xml](junit.xml), [coverage.json](coverage.json), [before-suite-receipt.json](before-suite-receipt.json), [verify.py](verify.py).
