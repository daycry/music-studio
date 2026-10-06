# QA CPU — arnés privado T-16, fix3

Fecha: 2026-10-06. **CONFORME CPU: 26 pruebas, cero fallos y cero avisos, exit0.** QA independiente de la implementación; contexto reutilizado de lente A/T-19 por límite de threads. No se afirma contexto fresco ni una segunda opinión con contexto independiente.

## Puertas sin UI

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`). `qa-gate.py` de Playwright no aplica ni se ejecuta; no se fabrican resultados E2E, capturas ni porcentaje E2E. La exención declarada no equivale a cobertura UI comprobada. No hay test-plan con escenarios E2E/M/API/A11Y.

`ledger-lint.py`: exit0, 0 incoherencias y 7 avisos Changelog:

```text
⚠️  T-08: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-09: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-10: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-11: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-12: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-13: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
⚠️  T-16: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
ledger-lint: 0 incoherencias · 7 avisos (tasks.md)
```

`coverage-check.py`: exit0; salida JSON real:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

Los veinte IDs listados en eximidos son tareas para revisión, `eximidos_exigidos=false`; no hay GWT exigidos eximidos. Sin rutas UI ni degradación detectadas. Cobertura del arnés privado efímero n/a; no se sustituye por el porcentaje histórico de producto ni se repite la suite430. Seis fuentes de producto siguen idénticas a la QA CPU anterior.

## Evidencia actual propia

| Verificación | Resultado |
|---|---|
| fix1+fix2+fix3, cache y basetemp propios | 26 passed in 0.81s, sin avisos, exit0; `pytest.txt` |
| Nueve SHA actuales/históricos/T15 del recibo fix3 | Todos coinciden; `hashes.json` |
| Seis fuentes de producto contra CPU QA histórico | Todos coinciden; `hashes.json` |
| Gramática AST Python3.11 | Nueve fuentes/snapshots conformes; runtime de tests Python3.12.14 |
| Runner `--prepare-only` | ready_cpu, configuración seis tomas90s, GPU false, exit0; `prepare-only.txt` |

Comando exacto de tests en [recibo QA](harness-fix3-qa-receipt.json). Comando de preparación: `uv run --frozen --all-packages python .cache/dev-cycle/t16/run-comparison.py --prepare-only`. Solo valida configuración/hashes e identidad mediante `docker image inspect` de lectura; no inicia contenedor, no realiza preflight GPU ni HTTP de generación. Digest: `sha256:9e4fc86fe17269ef80ad6649d9f80b02f8d1f0c7af160f3f9d0fde362dfd8f84`. El valor takes=6 describe configuración; **tomas ejecutadas/completadas por QA: cero**.

Los tests invocan preflight HTTP real en proceso con medidas GPU sintéticas, sin hijo ni job aceptado. Validan null explícito/campos ausentes/falsy, datos GPU inválidos, cap ausente tras carga y umbral95%, más doce regresiones H1–H4. Los bytes históricos y originales no se sobrescriben.

## Trazabilidad y precedentes

| Criterio | Estado |
|---|---|
| A-F2-01 | Corregido: presencia y None exacto; seis regresiones incluidas |
| Preflight válido, datos inválidos, carga real,95% | Conformes CPU dirigidos |
| H1–H4 | Doce regresiones conservadas |
| CA1/2 producto | Evidencia anterior conservada por hashes; no repetida |
| CA3/4 GPU/paquete/escucha | Pendientes; ninguna nueva inferencia ni calidad aprobada |

[Fix3](harness-fix3-report.md) y [recibo de fuentes](harness-fix3-receipt.json) conservan RED seis fallos previo y GREEN; [revisión intento2](harness-fix3-review-2.md) posterior acredita cero gaps. `review_complete=false` en el recibo fix3 es el snapshot creado **antes** de revisar, no el estado actual de la revisión. No se reescribe ese antecedente. [Revisión de fix2](harness-fix2-review-1.md) conserva el gap original. La QA actual comprueba comportamiento y hashes; no vuelve a ejecutar RED cambiando producción.

## Límites y checklist manual

- [ ] Retry GPU y seis tomas emparejadas reales, con telemetría/unload: pendientes.
- [ ] Paquete musical completo y escucha de obediencia/naturalidad: pendientes; sin ganador.
- [ ] UI/E2E cuando haya interfaz: fuera de M0 sin UI.
- [ ] PDF pendiente por dependencias de render ausentes; no se instala ni genera fuera del alcance autorizado.

Sin GPU, modelos, Docker escritura, instalaciones, audio original, fullpack ni jobs aceptables. No se cambian producto, ledger, Git, marcadores, documentos comunes ni knowledge. T-16 y CA3/4 siguen en-progreso; M0 abierto. Medición fuente estimado: tokens/coste/horas IA reales null; reloj y ventanas concurrentes no se suman como consumo IA.

Validación documental: seis informes/recibos, 9 enlaces locales válidos, cero hallazgos de privacidad/formato en el alcance indicado. No se comprobaron anchors ni fragmentos privados arbitrarios. Evidencia `docs.json`.
