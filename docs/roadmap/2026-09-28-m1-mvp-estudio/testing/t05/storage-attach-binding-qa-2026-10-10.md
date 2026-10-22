# Informe de QA — T-05 attach con binding

| Campo | Resultado |
|---|---|
| Fecha | 2026-10-10 |
| Componente | Conforme en alcance CPU y regresión Windows nativa |
| Estado global M1 | **NO-VERDE**; T-05 permanece abierta |
| URL auditada | No aplica: módulo nativo/CPU, sin UI ni servidor |
| Plan | [Plan](../../improvement-plan.md) · [Tests](../../test-plan.md) · [Ledger](../../tasks.md) |

## Veredicto y alcance

La QA actual del incremento integrado tras revisión A/B intento 2 pasa. No se ha ejecutado `qa-gate.py`: requiere resultados Playwright y no corresponde a este delta sin UI; no se fabrica JSON Playwright a partir de pytest. Las pruebas attach usan dobles CPU de administrador, binding y comandos; no acreditan compatibilidad WSL ni ejecución nativa de attach. Binding y storage_windows sí usan las API Windows sobre archivos testigo propios. No se ha usado GPU, Ollama, Docker, WSL, elevación, discos publicados reales ni datos canónicos.

Constitución §2 y ADR-0069: todos los artefactos y archivos testigo están dentro del proyecto. La persistencia ext4 y el montaje real siguen pendientes; ningún resultado CPU sustituye esas pruebas.

## Resultados automáticos y evidencia

| Ejecución | Resultado | Evidencia |
|---|---|---|
| Attach funcional actual | 72 PASS, 0 FAIL/ERROR/SKIP | [JUnit](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/attach-functional.xml) · [log](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/attach-functional.log) · [terminal exit 0](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/attach-functional.terminal.json) |
| Binding Windows nativo | 19 PASS, 0 FAIL/ERROR/SKIP | [JUnit](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/binding-native.xml) · [log](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/binding-native.log) · [terminal exit 0](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/binding-native.terminal.json) |
| Custodia Windows nativa | 14 PASS, 0 FAIL/ERROR/SKIP | [JUnit](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/windows-native.xml) · [log](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/windows-native.log) · [terminal exit 0](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/windows-native.terminal.json) |
| Attach medición corregida | 72 PASS, 0 FAIL/ERROR/SKIP | [JUnit](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/attach-coverage2.xml) · [log](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/attach-coverage2.log) · [terminal exit 0](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/attach-coverage2.terminal.json) |
| B01 causal independiente | API y CLI PASS; CLI exit 2 esperado | [probe](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/b01-probe2.json) · [log](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/b01-probe2.log) · [terminal exit 0](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/b01-probe2.terminal.json) |

B01: fallo primario propio en findmnt tras attach/mount simulado; rollback umount y detach propios, seguido de close fallido. API conserva `primary is __cause__`, cleanup_errors y notes; CLI mantiene NOT_READY/exit 2, causa original, BINDING_CLOSE_FAILED, incertidumbre/efectos/handles, sin exponer detalle privado de close. Close se intenta exactamente una vez y bytes del recibo permanecen iguales. El probe es independiente del escenario de tests existente; sólo sus comandos son dobles, no WSL real.

## Cobertura oficial del módulo completo

`coverage.py` mide **252/273 = 92.30769 %** de `scripts/storage_attach.py`, 21 líneas sin ejecutar, **0 exclusiones**, sin ramas medidas. Gate oficial `coverage report --fail-under=80`: exit 0. Se incluye importación del módulo antes de pytest bajo instrumentación; imports explícitos y comprobados desde snapshot, sin module-cache del checkout.

[JSON oficial](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/coverage2.json) · [reporte oficial](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/coverage-report2.log) · [terminal gate](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/coverage-report2.terminal.json) · [runner](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/runner.py) · [config sin exclusiones](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/snapshot/coverage.ini).

## Puertas del plan y trazabilidad

Ledger-lint exit 0: 0 incoherencias, 1 aviso por fichero no UTF-8 limpio. [salida](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/ledger-lint.log) · [terminal](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/ledger-lint.terminal.json).

Coverage-check exit 0: broken_refs 0; tests_sin_referencia []; tareas_sin_cobertura [T-00]. T-00 es secuenciación documental sin UI, con bloque DOC-00 explícito del test-plan; el aviso se conserva. No hay GWT huérfanos según la puerta. [salida completa](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/coverage-check.log) · [terminal](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/coverage-check.terminal.json).

T-05 mantiene E2E-01, E2E-09 y M-01 del plan. Esta ejecución aporta sólo evidencia técnica attach-binding y regresión nativa, **0 E2E nuevos**, 0 API/A11Y nuevos. No repite suites de otras unidades ni modifica estados/checkboxes. Consulta de gotchas sin aciertos; README conocido, sin gotcha nueva.

## Intentos fallidos conservados

- Medición inicial: 72 PASS, pero source absoluto fue interpretado como nombre de módulo por Coverage; no recolectó datos. JSON/reporte oficiales exit 1 y warnings guardados. [log inicial](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/attach-coverage.log) · [JSON exit 1](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/coverage-json.terminal.json) · [reporte exit 1](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/coverage-report.terminal.json) · [runner inicial](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/runner-coverage-attempt1.py).
- Lanzador de corrección: fallo BOM del `exec(read_text())`, exit 1 observado en herramienta, sin iniciar pytest. [recibo](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/coverage2-launch-bom.terminal.json) · [resumen del fallo](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/coverage2-launch-bom.log). El log es resumen, no transcripción exacta; el traceback exacto vive en la salida de herramienta.
- Primer probe independiente: error del arnés al consultar atributo inexistente del recibo; exit 1 preservado. Se corrigió sólo arnés a UUID del plan y nuevo directorio propio. [log original](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/b01-probe.log) · [terminal exit 1](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/b01-probe.terminal.json) · [probe original](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/probe_b01.py).

## Sellos y reproducibilidad

16 fuentes/dependencias/configuraciones originales protegidas antes/después; todos los Python del snapshot son copias byte a byte. Fuentes actuales attach SHA `31ee85f23c76b148079d37ee30fd34e0ca0bc21defcdbdd6b5c4d7ebbf561358` y test SHA `83c9f8057bcba63d75237319566195b8e4185f54dc4861d3d825ee38419da9bc`. Dependencias binding/windows/receipt coinciden con recibo de integración. Sello final **SOURCE_SEAL_FINISHED**.

[pre-sello](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/sources-before.json) · [post-sello](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/sources-after.json) · [sello final](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/SOURCE_SEAL_FINISHED.json) · [inventario SHA/tamaño](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/inventory.json) · [comandos/runner de ejecución](../../../../../.cache/dev-cycle/m1/storage-attach-binding-20261010/qa/run_all.py).

Entorno gestionado del repo: `scripts/env.ps1`, `uv run --frozen --no-sync --all-packages python -B`; basetemp/cache/COVERAGE_FILE y padres confinados en QA propia. Todos los códigos reales de procesos ejecutados están en terminales; los lanzadores de lote no sustituyen dichos códigos. Sin instalaciones ni cambios en dependencias. PDF no generado: renderer gestionado no disponible en este alcance; no se instalaron dependencias. Uso medido por orquestador a nivel lote; tokens/coste reales desconocidos, sin sumar estimaciones individuales.

## Checklist pendiente

- [ ] Attach nativo con autoridad administrativa, montaje ext4/UUID y compatibilidad WSL real.
- [ ] Recibo con CAS/durabilidad y controller completo validated/detach; la lectura/comprobación/escritura por pathname no resuelve estas propiedades.
- [ ] Publicación persistente, restart/recovery, assets/Range y backup/restauración real.
- [ ] M-01 GPU y escucha humana; M-02 revisión visual/accesibilidad; M-03 backup/restauración.
- [ ] Integración Git y aceptación formal del hito por orquestador.

No se cierra T-05/M1 ni se hace handoff de cierre a documenter.
