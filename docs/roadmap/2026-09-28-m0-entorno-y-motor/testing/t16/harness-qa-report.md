# T-16 — QA independiente del arnés corregido

Fecha: 2026-10-06. **Conforme CPU acotado: 12/12 casos, cero fallos y cero avisos, exit 0.** No es un verde E2E ni el cierre de T-16/M0. [Recibo verificable](harness-qa-receipt.json); antecedente: [revisión A+B, intento 2](harness-review-2.md).

Se verifican únicamente runner, packer, helper CLI y test privado corregidos. El producto CPU ya aprobado no se volvió a probar ni construir: sus seis fuentes conservan los SHA-256 del [recibo CPU anterior](cpu-qa-receipt.json). Los recibos anteriores permanecen como históricos, incluido el campo de revisión pendiente del recibo de corrección.

| Caso dirigido | Cantidad | Resultado y evidencia |
|---|---:|---|
| Timeouts de arranque/logs/stop: finally y limpieza por ID propio | 3 | Pasan con dobles Docker sobre AST actual |
| Job ajeno detectado durante monitor y lectura final | 2 | Pasan: sin stop/rm y cleanup diferido registrado |
| Etiqueta o imagen ajena | 2 | Pasan: identidad rechazada y contenedor preservado |
| Referencia interrumpida y reintento | 1 | Pasa: hardlink atómico y fuente intacta |
| Destino y temporal ajenos | 2 | Pasan: no se sustituyen |
| Globals del validador MP3, incluido math | 1 | Pasa con doble FFprobe |
| FFprobe real sobre senoide sintética existente de 90 s | 1 | Pasa: 48 kHz, estéreo, duración dentro de tolerancia |

Evidencia privada: `.cache/dev-cycle/t16/qa-harness/pytest.txt`, `hashes.json` y `prepare-only.txt`. Comando ejecutado tras cargar `scripts/env.ps1`:

```powershell
uv run --frozen --all-packages pytest .cache/dev-cycle/t16/test_harness_fix1.py -q -o cache_dir=.cache/dev-cycle/t16/qa-harness/pytest-cache --basetemp .cache/dev-cycle/t16/qa-harness/pytest-temp
```

```text
12 passed in 0.49s
```

Runtime local Python 3.12.14; AST con gramática 3.11 válido para cuatro fuentes, sin afirmar ejecución real en Python 3.11. Cuatro SHA actuales y dos snapshots históricos coinciden con `harness-fix1-receipt.json`; el séptimo SHA, supervisión T-15, coincide con el valor fijado por runner y packer. La fixture local puede redirigir tmp_path al directorio de temporales del repositorio. No se tocaron originales musicales ni audio de referencia real.

`run-comparison.py --prepare-only`: exit 0, `ready_cpu`, seis tomas previstas de 90 s, imagen existente validada por digest, sin contenedores ni jobs. Solo inspección de imagen; no ejecución de guardas GPU. Baseline continúa en 1.600 MiB y la excepción de permiso sigue pendiente.

ℹ️ **Sin UI por diseño (`test-plan: n/a (sin UI)`).** `ledger-lint`: exit 0, **0 incoherencias y 7 avisos** de Changelog (T-08…T-13 y T-16). `coverage-check`: exit 0; puerta de cobertura no ejecutada, no se presenta como cobertura OK. Salida JSON:

```json
{
  "applies": false,
  "gwt_sin_id": 0,
  "test_plan_na": true,
  "marcador_no_canonico": null,
  "eximidos": [
    "T-00",
    "T-01",
    "T-02",
    "T-03",
    "T-04",
    "T-05",
    "T-06",
    "T-07",
    "T-08",
    "T-09",
    "T-10",
    "T-11",
    "T-12",
    "T-13",
    "T-14",
    "T-15",
    "T-16",
    "T-17",
    "T-18",
    "T-19"
  ],
  "eximidos_exigidos": false,
  "rutas_ui": [],
  "rutas_ui_origen": {},
  "rutas_ui_degradado": null
}
```

`qa-gate.py`: **n/a por diseño**, sin results E2E; no se fabricó salida de gate ni porcentaje de cobertura. Sin API/A11Y/UI en este alcance privado. El porcentaje unitario de producto anterior no se reinterpreta como cobertura del arnés. PDF pendiente por dependencias de render ausentes en la QA CPU anterior y restricción de no instalar; no se generó un PDF.

Pendientes manuales/de ejecución:

- [ ] Autorización y guardas antes de cualquier ejecución GPU; baseline fijo, sin ampliar permisos desde esta QA.
- [ ] CA3: seis generaciones reales emparejadas, telemetría, cancelación/descarga y limpieza real.
- [ ] Paquete musical completo real; no se ejecutó siquiera un full pack sintético.
- [ ] CA4: escucha privada ciega y aprobación musical por el propietario.

Los dobles y fragmentos AST acreditan estos doce casos; no prueban la integración completa runner/packer, Docker real, carreras no modeladas, GPU ni calidad musical. No hay ganador ni cierre CA3/4. Root conserva la actualización del ledger y publicación de rama; no se integra en main ni se hace handoff de cierre a documenter. Jira/Confluence no aplican. Consumo: fuente estimada; tokens, coste y horas IA reales desconocidos (`null`).

Validación documental: cuatro informes/recibos del arnés, 4 enlaces locales válidos; sin rutas personales, patrones de token ni texto completo de letra/estilo privado. No se comprobaron anchors ni fragmentos arbitrarios. Diff-check de los informes de revisión y QA exit 0; los outputs nuevos también se comprobaron directamente para espacios finales y marcadores de conflicto.
