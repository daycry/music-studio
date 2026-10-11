---
agent: qa
model_tier: sonnet
effort: medium
tier_source: release-root.receipt.json / frontmatter
actual_usage: null
scope: componente K1; sin aceptación K1/T-05/M1
---
# QA2 independiente de K1 — 2026-10-11

**VERDE en el alcance del componente**: Windows 116 PASS; Linux 106 PASS y 10 SKIP legítimos de plataforma; cero fallos, errores o flaky. Ruff check y format check de cuatro fuentes, ambos `--no-cache`, exit 0. No acepta K1, no ejecuta CAS ni cierra T-05/M1. Manuales y validación integral permanecen pendientes.

## Fuentes y revisión

27 fuentes privadas fijadas por [release ROOT](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/release-root.receipt.json), SHA verificados antes y después de cada ejecución. Revisión3 A/B limpia leída con sus tablas completas anteriores en [prior-review](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/prior-review.md); A01=B01 corregido. FIX2 sólo formato del test IO: el resultado actual se atribuye al SHA b1e23428; QA1 con test e2a249fd permanece histórico, sin reutilizar raw como ejecución nueva. Constitución: confinamiento al proyecto y custodia de memoria; no archivos NT, ACL, RootContext, administración, GPU, pesos, instalación o servicios.

| Fuente | SHA-256 |
|---|---|
| `scripts/storage_journal_windows_io.py` | `0d23e8f6d44ddd0b98ebeb6eef7e068bc0911c8fe95d61d3baeefad105af9de8` |
| `scripts/storage_journal_windows_abi.py` | `6a444d031fba168e93a43cb2de214dcdb84dfed08d6d304434b3607e48718ffe` |
| `tests/test_storage_journal_windows_io.py` | `b1e234289d934dd511044ab3eaee3a6aa13984a1aac26c55a98c1703a50e54b0` |
| `tests/test_storage_journal_windows_abi.py` | `d55fba92c093289cf2d0debad6f81b4435bc4b7dafb0b2ac9b6e156a8fdf437a` |

## Pruebas y evidencia

Ejecuciones frescas sobre los archivos originales readonly, sin selectores de exclusión: config propia UTF-8 sin BOM, `--noconftest`, `--confcutdir`, cacheprovider desactivado y JUnit xunit1. [Mismos 116 nodos y outcomes](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/same-nodes.json). Los conftests del resto de la aplicación no pertenecen al scope privado. Versiones, argv, imports reales completos y SHA están en los recibos. Todos los módulos de producto importados son IO/ABI del snapshot; ningún módulo de producto de la imagen sustituye a los originales.

| Plataforma | PASS | FAIL/ERROR | SKIP | Evidencia |
|---|---:|---:|---:|---|
| Windows, entorno gestionado env.ps1/uv, sin instalación | 116 | 0 | 0 | [JUnit](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/windows/junit.xml), [raw](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/windows/pytest.stdout), [recibo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/windows/run-receipt.json), [imports](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/windows/imports.json) |
| Linux CPU Docker real | 106 | 0 | 10 | [JUnit](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/linux/junit.xml), [raw](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/linux/pytest.stdout), [recibo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/linux/run-receipt.json), [imports](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/linux/imports.json) |

Windows: cuatro positivos nativos reales (`test_native_backend_complete_abi` y `test_native_own_memory_positive[512/4096/65536]`); otros seis controles específicos Windows. Sólo VirtualAlloc/Free/copias/binder en memoria propia, sin invocar NTCreate ni I/O. Supervisión nueva READY→GO→DONE→FINISH con nonce y CIM vivo acredita launcher→PID real os.getpid del intérprete; espera y ausencia de ambos, no deducidas únicamente de Popen. [Supervisión](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/supervision/receipt.json), [CIM vivo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/supervision/ready-cim.stdout), [CIM final](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/supervision/after-exit-cim.stdout).

Tres controles adicionales privados, fuera de JUnit, verifican independencia de bytes después de sobrescribir la arena, geometrías B512/B4096/B65536, liberación de base original×1, cierre idempotente, charge `(0,0,0)`, sin inflight y registro closed conservado. [Resultado](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/windows-private-native/private-native-result.json), [supervisión propia](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/supervision-private-native/receipt.json).

Linux extra privado: factories originales rechazan PLATFORM_UNSUPPORTED en plataforma real, cero intentos ctypes bajo guard de import; sin DLL/alloc/calls. [Sonda](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/linux/private-linux-unsupported.json). Los diez SKIP se conservan como SKIP:

- `test_native_own_memory_positive[512]` — Windows AMD64 real requerido; no positivo fingido
- `test_native_own_memory_positive[4096]` — Windows AMD64 real requerido; no positivo fingido
- `test_native_own_memory_positive[65536]` — Windows AMD64 real requerido; no positivo fingido
- `test_factory_abi_error_sanitized_before_resources` — Windows AMD64 real requerido; no positivo fingido
- `test_poison_blocks_native_factory_before_binder` — Windows AMD64 real requerido; no positivo fingido
- `test_native_backend_complete_abi` — Windows AMD64 real requerido; no positivo fingido
- `test_invalid_width_rejects_before_dll` — Windows AMD64 real requerido; no positivo fingido
- `test_missing_symbol_rejects_before_allocate` — Windows AMD64 real requerido; no positivo fingido
- `test_closed_native_arguments_normalization[65536-2-None]` — Windows AMD64 real requerido; no positivo fingido
- `test_closed_native_arguments_normalization[None-0-8]` — Windows AMD64 real requerido; no positivo fingido

Docker: imagen existente fijada `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`, runtime `/studio/.venv/bin/python`; `--rm`, red none, snapshot readonly y salida propia RW. [argv](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/linux-docker-argv.json), [inspect vivo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/linux-live-inspect.stdout), [wait0](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/linux-wait.stdout), [retirada](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/linux-after-inspect.stderr). Sin build/pull/retag, puertos, GPU, stops o prune.

## Cobertura oficial completa

coverage.py branch=True, sin omit/exclude_lines/partial_branches y archivos completos. La combinación oficial `CoverageData.update(map_path=...)` normaliza sólo las rutas de dos fuentes con SHA idénticos; no promedia porcentajes. ABI Linux real es 51,4286 %, por debajo del 80 %; Windows y la combinación cubren **cada archivo** sobre el 80 %.

| Datos | Archivo completo | Líneas | Ramas cubiertas/total | Exclusiones |
|---|---|---:|---:|---:|
| windows | `storage_journal_windows_abi.py` | 70/70 (100.0000 %) | 10/10 | 0 |
| windows | `storage_journal_windows_io.py` | 370/376 (98.4043 %) | 100/108 | 0 |
| linux | `storage_journal_windows_abi.py` | 36/70 (51.4286 %) | 4/10 | 0 |
| linux | `storage_journal_windows_io.py` | 361/376 (96.0106 %) | 97/108 | 0 |
| combined | `storage_journal_windows_abi.py` | 70/70 (100.0000 %) | 10/10 | 0 |
| combined | `storage_journal_windows_io.py` | 370/376 (98.4043 %) | 100/108 | 0 |

[Whole por archivo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/whole.json), [JSON oficial combinado](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/combined/coverage.json), [datos oficiales](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/combined/.coverage). Pirámide medida en este scope: unitario de archivos completos según tabla; E2E UI no ejecutado/no medido.

## Gates deterministas

Adaptador transparente JUnit→results.json con provenance/SHA del JUnit, mismos nodos/outcomes y skips intactos. No es ejecución Playwright ni E2E UI. Scripts oficiales plugin 1.21.1 sin modificar.

Windows qa-gate exit 0:

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 116,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

Linux qa-gate exit 0:

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 106,
    "failed": 0,
    "flaky": 0,
    "skipped": 10,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

Ledger-lint exit 0: 0 incoherencias, aviso original de UTF-8 no limpio preservado. [Raw](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/ledger-lint.stdout).
Coverage-check exit 0: referencias rotas 0 y GWT huérfanos 0; aviso T-00 sin cobertura. [Raw completo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/coverage-check.stdout). Ledger documenta T00→DOC-00, prefijo no reconocido por el parser; no constituye aprobación UI global. M1 conserva test-plan con UI, sin marcador global «sin UI».
Ruff check4 y format4 `--no-cache`: exit0/exit0, [check](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/ruff-check.stdout), [format](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/ruff-format-check.stdout). El format1 de QA1 permanece histórico, no fue sobrescrito.

## Diagnósticos propios preservados

Primer contenedor QA2: el harness supuso `/app/.venv/bin/python`; ruta inexistente, exit127 antes de ejecutar el producto. [Stderr](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/attempt1-linux-wrapper.stderr), [inspect](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/attempt1-linux-live-inspect.stdout), [wait](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa2-20261011/attempt1-linux-wait.stdout). Runner original y traceback propios conservados; intento2 corrigió sólo el harness a `/studio/.venv/bin/python`. No es un fallo del producto y no se contabiliza como caso ejecutado. Primera conversión PDF no encontró el Chromium por defecto; stderr/exit conservados en pdf-attempt1. Se usó después el Chromium existente del repositorio, sin descargar ni instalar.

## Manuales y estado pendiente

- [ ] M-01/M-02/M-03 del test-plan M1.
- [ ] E2E/API/UI integral M1, ext4 persistente real y recuperación causal.
- [ ] K2–K5/store/ACK/S1 full-chain/bootstrap/lifecycle y adopción/CAS ROOT.

Sin escrituras de app, contratos, ledger, frontmatter del plan, Git, locks o meters. Evidencia sólo local, sin Confluence/Jira ni handoff a documenter. Uso real tokens/coste/horas IA null. Esta QA demuestra únicamente el alcance K1 autorizado; T-05 y M1 siguen abiertos.
