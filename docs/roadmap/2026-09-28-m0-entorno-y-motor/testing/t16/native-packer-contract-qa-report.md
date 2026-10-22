# QA independiente: contrato packer T-16

Resultado **conforme para el contrato CPU acotado**: 9/9 pruebas independientes, cero fallos/errores/omisiones (qa.xml). No es un veredicto E2E ni un cierre de T-16/M0.

El bloque completo de validación de seis elementos usa los seis manifiestos reales y seis recibos nativos v2, con `audio_post.manifest.validate_input_receipt` real e intacto. La versión baseline reproduce `KeyError: 'request'`; el candidato continúa y conserva el conjunto semillas1/2/3 × Turbo/SFT. Cada conflicto posterior al validador (modelo, checkpoint, steps, CFG, caption, LM, DiT y metadata) termina en la guarda específica esperada. Los dobles de `SoundFile`, `measure_audio` y `verify_manifest` no abren audio ni verifican codec, duración o normalización.

Integridad: 87 rutas de freeze originales intactas y null preservados; candidato, tests entregados, review-final y metadata6+6 añadidos al freeze QA. SHA candidato `182e7f91db261cd431ec552670a86ef81162b9f67ab95335f9f27496fc2f2edf`. Artefactos de entrega verificados contra sus hashes; JUnit RED1 fallo de contrato, GREEN9 y QA9 comprobados. RED anterior al GREEN; se corrobora la secuencia registrada, sin atribuir timestamps actuales a pruebas TDD nuevas. A+B+C+D ya conformes en review-final; QA no sustituye esas revisiones.

`ledger-lint`: exit0, 0 incoherencias, 6 avisos de Changelog futuro. ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`): coverage-check exit0 acepta la declaración, no ejecuta la puerta de cobertura. Lista T-00…T-19 para revisión; no exigidos. Sin rutas UI detectadas ni degradación declarada. Salida JSON literal:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

qa-gate no ejecutado / no aplicable, porcentaje null:

```json
{"executed": false, "applies": false, "percentage": null, "reason": "test-plan: n/a (sin UI)"}
```

Evidencia: [JUnit QA](../../../../../.cache/dev-cycle/t16/native-packer-contract-qa/qa.xml), [salida](../../../../../.cache/dev-cycle/t16/native-packer-contract-qa/qa.stdout.txt), [recibo](../../../../../.cache/dev-cycle/t16/native-packer-contract-qa/receipt.json), [freeze antes](../../../../../.cache/dev-cycle/t16/native-packer-contract-qa/freeze-before.json), [freeze después](../../../../../.cache/dev-cycle/t16/native-packer-contract-qa/freeze-after.json), [ledger](../../../../../.cache/dev-cycle/t16/native-packer-contract-qa/ledger-output.txt), [cobertura](../../../../../.cache/dev-cycle/t16/native-packer-contract-qa/coverage-output.txt). Comando portable: cargar `scripts/env.ps1`, fijar PYTHONUTF8=1 y PYTHONDONTWRITEBYTECODE=1; `uv run --frozen --all-packages --no-sync python .cache/dev-cycle/t16/native-packer-contract-qa/run_qa.py`. Entorno administrado, sin sincronizar ni instalar.

PDF pendiente: no se encontró renderer to-pdf instalado dentro del repo; no se instalaron dependencias ni se usaron directorios de usuario. No UI/screenshots ni checklist M-xx en esta iniciativa.

Pendientes para root: publicar fusión revisada, actualizar puntero tras aceptación, ejecutar primer fullpack corregido y validar audio real/niveles/pares/cap-spill actuales. Sin fullpack, GPU, jobs, modelos, audio, modificación de producto, ledger, Git ni datos. CA3/CA4, escucha, calidad y M0 permanecen abiertos; sin handoff. Métricas fuente estimada, tokens/EUR/horas null y ninguna ventana nueva.
