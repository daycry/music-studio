# QA independiente — T-05 PublishedDiskBinding — 2026-10-10

**VERDE del componente nativo; T-05 y M1 NO-VERDE.** 19/19 funcionales, 19/19 con cobertura y regresión 17/17, sin omisiones. Evidencias propias, no reutilizadas de implementador/revisión. Windows 11, Python gestionado 3.12.14, `uv run --frozen --no-sync --all-packages`; ningún lock/install/Docker/WSL/GPU/admin alterado. Fuentes de producto sólo lectura.

## Gate nativo reproducible

`qa-gate.py` no aplica: consume resultados Playwright, mientras este delta es un módulo nativo sin UI/HTTP. No se han fabricado estadísticas, capturas ni resultados E2E. La decisión limitada se obtiene de JUnit reales, coverage JSON y sellos con [finalize.py](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/finalize.py). [Gate completo](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/native-gate.json), [terminal](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/native-gate-terminal.json).

```json
{
  "verdict": "VERDE-COMPONENTE",
  "scope": "PublishedDiskBinding, Windows nativo; no aceptación T-05/M1",
  "whole_operator": {
    "covered_lines": 118,
    "num_statements": 125,
    "percent_covered": 94.4,
    "percent_covered_display": "94",
    "missing_lines": 7,
    "excluded_lines": 0,
    "percent_statements_covered": 94.4,
    "percent_statements_covered_display": "94"
  },
  "module_operator": {
    "covered_lines": 118,
    "num_statements": 125,
    "percent_covered": 94.4,
    "percent_covered_display": "94",
    "missing_lines": 7,
    "excluded_lines": 0,
    "percent_statements_covered": 94.4,
    "percent_statements_covered_display": "94"
  },
  "threshold": 80,
  "excluded_lines": 0,
  "source_unchanged": true,
  "independent_entry_failure": true,
  "qa_gate_py": "NO APLICA: formato Playwright no corresponde a pytest nativo; no resultados sintéticos",
  "T05_M1": "NO-VERDE: persistencia ext4/publicación/workers/manifest/manuales pendientes",
  "functional": "19/19 PASS",
  "coverage_execution": "19/19 PASS",
  "dependency_regression": "17/17 PASS"
}
```

WHOLE y módulo completo `scripts/storage_operator.py`: **118/125 = 94,4 %**, umbral 80 %, **0 exclusiones**. No se mide sólo diff ni función parcial. Faltan líneas 45,78,197,217,221,238,239; incluyen errores de plataforma y fallo de cleanup, no demostrados. [coverage.json](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/coverage.json). El test de entrada fallida pasa; no se afirma cobertura de fallo nativo CloseHandle.

## Ejecuciones y aislamiento

[Funcional JUnit](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/native-functional.xml), [terminal](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/native-functional-terminal.json); [cobertura JUnit](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/native-coverage.xml), [terminal](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/native-coverage-terminal.json); [regresión JUnit](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/native-regression2.xml), [terminal](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/native-regression2-terminal.json). [stdout funcional/cobertura/primera regresión](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/run.stdout.txt), [stdout regresión corregida](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/regression2.stdout.txt).

Snapshot byte a byte de fuentes y tests; contexto real `storage_windows` y paquete local `receipt`. `_PRIVATE` se redirige **en memoria sólo en collection** para que fixtures exclusivos escriban dentro de snapshot QA; se conserva el archivo test y todos sus asserts. Win32 no se simula. Los tests originales de carreras interceptan Python y llaman API nativa original, según código sellado.

Primera regresión: 3 PASS de publicación y 14 ERROR de setup porque el arnés no había creado el padre privado que exige fixture `path.mkdir()` sin `parents=True`. Se conserva [JUnit inicial](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/native-regression.xml) y su exit1. Segunda regresión sólo crea ese padre propio y ejecuta los **mismos tests sellados**, 17/17 exit0. Ningún fallo de producto ocultado. La regresión `storage_windows` prueba creación/identidad/sparse/seal/promoción/disposición/leases/hijos nativos; `storage_publish` tiene 3 tests con FakeCustody, por tanto es lógica unitaria de publicación, no validación VHDX/ext4.

## Reproducciones independientes

Entrada fallida por mutación de recibo tras open correcto, sin monkeypatch Win32: **handles 235 → 254 → 235**, close idempotente 235; cuerpo no entró, excepción preservada `recibo alterado durante binding`, rename tras fallo permitido. SHA extranjero antes/después `282f3d66ca5460be08c400ec81240a88a1df79d3effedac355a7a4a0836d12d4` idéntico. [Recibo](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/independent-entry-failure.json).

Lease normal: FileID real validado, delete WinError32 durante lease, cierre devuelve handles **235 → 235**, rename posterior permitido. [Recibo](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/independent-normal.json). No fixture ni handle ajeno eliminado. Testigos, junctions y archivos sparse propios se conservan; productores propios en regresión son reapados por tests, sin cambiar servicios.

## Escenarios focales

Todos PASS con evidencia en ambos JUnit:

- test_live_query_identity_and_runtime_writes
- test_replacement_before_open_preserves_foreign
- test_lease_blocks_real_rename_delete_and_releases_exactly
- test_hardlink_rejected_without_leak_or_writes
- test_bad_receipt_evidence_rejected_without_leak[file_id-0:00000000000000000000000000000000]
- test_bad_receipt_evidence_rejected_without_leak[file_id-invalid]
- test_bad_receipt_evidence_rejected_without_leak[final_path-C:/foreign.vhdx]
- test_receipt_mutation_during_acquisition_is_rejected
- test_reparse_ancestor_rejected
- test_path_replacement_during_acquisition_rejected
- test_disk_reparse_rejected_without_writes
- test_unc_relative_and_noncanonical_roots_rejected[relative]
- test_unc_relative_and_noncanonical_roots_rejected[C:/with/../escape]
- test_unc_relative_and_noncanonical_roots_rejected[//server/share/project]
- test_unc_relative_and_noncanonical_roots_rejected[C:/bad.]
- test_public_constructor_wrong_receipt_phase_and_type_rejected
- test_missing_disk_releases_every_retained_handle
- test_receipt_mutation_after_open_rejected
- test_entry_failure_releases_native_handles_and_preserves_foreign

## Puertas de trazabilidad

Ledger-lint exit0, 0 incoherencias; aviso UTF-8 preexistente registrado, sin corregir ledger. Coverage-check exit0, 0 referencias rotas, GWT sin cubrir vacío. Advertencia T-00 sin cobertura: tarea documental de apertura técnica, no UI de este delta; se conserva aviso. [Terminal ledger](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/ledger-lint-terminal.json), [terminal coverage-check](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/coverage-check-terminal.json).

```
⚠️  el fichero no es UTF-8 limpio (leído con reemplazos)
ledger-lint: 0 incoherencias · 1 avisos (tasks.md)
⚠️  T-00: sin cobertura declarada (si es tarea de UI, es un criterio huérfano → NO verde)
{"applies": true, "defined": ["API-01", "API-02", "E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "M-01", "M-02", "M-03"], "referenced": ["API-01", "API-02", "E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "M-01", "M-02", "M-03"], "broken_refs": 0, "tasks_sin_cobertura": ["T-00"], "tests_sin_referencia": [], "gwt_cubiertos": [], "gwt_sin_cubrir": [], "gwt_sin_id": 0, "test_plan_na": false, "marcador_no_canonico": null}
```

Lectura Constitución: almacenamiento dentro de proyecto y evidencia nativa limitada; no abrir `data/_storage/studio-data.vhdx` real ni afirmar persistencia. Knowledge-find contextual exit0 sin resultados; barrido gotcha limit0 conservado, no flaky ni nuevo gotcha.

## Sellos y límites

[SHA antes](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/source-before.json), [SOURCE_SEAL_FINISHED](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/SOURCE_SEAL_FINISHED.json): 8 fuentes/contexto/test byte a byte intactos después; operator `47f20bcbb9c76ef261dae799ab6308ac83aced98b31ff08b1b55cb1bcf3c56b8`, test `ccb424107c91a03fc395299e0374994a15533d464bfa2eddfc92373355b8c741`, dependencia Windows `f15d43737a94bd4e7ac484df920f2d14fd6b936141936d100aff73e6dc648d90`. Snapshot conserva idénticos hashes. [Inventario de evidencias](../../../../../.cache/dev-cycle/m1/storage-binding-20261010/qa/inventory.json): ruta, tamaño y SHA-256.

PDF omitido explícitamente: no renderer to-pdf gestionado usable en tools/cache del proyecto; tampoco cache preexistente de skill. No se instala ni escribe fuera del repo. Informe Markdown entregado. Tokens/coste reales **null** (sin transcript); duración desde inicio facilitado 20:41:11Z, medición temporal en `usage.json`, no token estimado presentado como real.

## Checklist pendiente para aceptación T-05/M1

- [ ] Controlador validated/detach y almacenamiento persistente ext4/VHDX real.
- [ ] Publicación/workers/manifest/recovery/assets/Range sobre ese almacenamiento real.
- [ ] M-01 generación GPU y escucha humana.
- [ ] M-02 revisión visual/accesibilidad.
- [ ] M-03 backup/restauración real.

No handoff documenter ni cierre del plan/spec/ledger: corresponde a root aceptar evidencia del componente y conservar aceptación integral pendiente.
