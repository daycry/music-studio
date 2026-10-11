# QA independiente de T-05 / K1 — candidato actual, 2026-10-11

Los gates automáticos del componente son **VERDE**: Windows 116 PASS, Linux 106 PASS y 10 SKIP de plataforma, sin fallos ni flaky. **La conformidad de formato queda pendiente** (`ruff format --check`: exit 1). Esta evidencia no acepta K1, no cierra T-05 y no valida M1. La adopción/CAS y la adjudicación del formato corresponden a ROOT.

## Alcance y fuentes

Candidato privado bajo `snapshot/`, fijado por el [release ROOT](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/release-root.receipt.json), 27 preimágenes verificadas antes y después. Revisión2 A/B limpia, A01=B01 corregido, tabla completa leída en [prior-review](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/prior-review.md). Contratos leídos: kernel C2, store O2, ADR-0081 y fronteras constitucionales. No se atribuye el testigo histórico de SHA ad8 al candidato actual.

| Archivo | SHA-256 |
|---|---|
| `scripts/storage_journal_windows_io.py` | `0d23e8f6d44ddd0b98ebeb6eef7e068bc0911c8fe95d61d3baeefad105af9de8` |
| `scripts/storage_journal_windows_abi.py` | `6a444d031fba168e93a43cb2de214dcdb84dfed08d6d304434b3607e48718ffe` |
| `tests/test_storage_journal_windows_io.py` | `e2a249fd314f73445c57e687ccdcf4e25b77f3e6bd5963f30addf75fddcb95eb` |
| `tests/test_storage_journal_windows_abi.py` | `d55fba92c093289cf2d0debad6f81b4435bc4b7dafb0b2ac9b6e156a8fdf437a` |

## Ejecuciones y trazabilidad

Los mismos 116 identificadores de JUnit aparecen en ambas plataformas. Los archivos originales se ejecutaron directamente desde el snapshot, sin cambios ni selectors: `--noconftest`, config privada, `junit_family=xunit1`, cacheprovider desactivado. Se evita importar conftests que necesitan módulos ajenos no incluidos en este snapshot. Se conservaron argv, versiones, imports/SHA, preimágenes, cobertura oficial, stdout/stderr y códigos. No hubo instalaciones. Windows usó el entorno gestionado por `env.ps1` y `uv --frozen --no-sync`; Linux el intérprete CPU ya existente en imagen fijada.

| Plataforma | PASS | FAIL/ERROR | SKIP | Evidencia |
|---|---:|---:|---:|---|
| Windows | 116 | 0 | 0 | [JUnit](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/windows-attempt2/junit.xml), [raw](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/windows-attempt2/pytest.stdout), [recibo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/windows-attempt2/run-receipt.json) |
| Linux Docker real, ejecución inspeccionada | 106 | 0 | 10 | [JUnit](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/linux-inspected/junit.xml), [raw](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/linux-inspected/pytest.stdout), [recibo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/linux-inspected/run-receipt.json) |

La primera ejecución Linux también tuvo 106 PASS/10 SKIP; se conserva por separado, sin sumar casos repetidos. La ejecución inspeccionada añadió evidencia contemporánea de configuración y retirada del contenedor. Imagen `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`, `--rm`, red `none`, snapshot montado readonly y salida propia RW. [Inspect](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/linux-inspected2.container-inspect.json), [wait](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/linux-inspected2.wait.stdout), [ausencia final](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/linux-inspected2.after-inspect.stderr). Sin GPU, puertos, servicios, builds, pulls o retags.

Todos los imports originales del componente corresponden a rutas/SHA del snapshot: [Windows](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/windows-attempt2/imports.json), [Linux](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/linux-inspected/imports.json). No se sustituyeron fuentes con las de la imagen.

### Cuatro positivos nativos de los 116 casos

| Caso | Resultado y evidencia |
|---|---|
| `test_native_backend_complete_abi` | PASS, binder/ABI real sin invocar I/O de archivos |
| `test_native_own_memory_positive[512]` | PASS, memoria propia exacta, base original liberada una vez, cierre idempotente, charge 0 |
| `test_native_own_memory_positive[4096]` | PASS, mismas condiciones |
| `test_native_own_memory_positive[65536]` | PASS, mismas condiciones |

La relación Windows launcher → runtime se comprobó viva mediante CIM y nonce antes de GO y después de las pruebas, con handshake FINISH y espera. Ambos procesos resultaron ausentes al cierre: [supervisión](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/supervision-attempt2/receipt.json), [CIM vivo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/supervision-attempt2/ready-cim.stdout), [CIM final](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/supervision-attempt2/after-exit-cim.stdout). No se atribuye ownership o reap únicamente al PID de Popen.

Tres controles **privados adicionales**, fuera del JUnit 116, verifican bytes independientes después de sobrescribir la arena, B512/4096/65536, base original×1, cierre idempotente, cuotas `(0,0,0)` y registro retenido en estado closed. [Resultados](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/windows-private-native2/private-native-result.json), [supervisión nueva](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/supervision-private-native2/receipt.json). No conceden capacidades de archivo, trust, grants o ACK.

### Skips Linux reales

La predicción inicial de ROOT de cuatro skips se corrigió: cuatro positivos nativos más seis controles específicos Windows. No se fingió plataforma, no se retocaron tests ni se convirtieron skips en PASS.

- `test_native_own_memory_positive[512]` — Windows AMD64 real requerido.
- `test_native_own_memory_positive[4096]` — Windows AMD64 real requerido.
- `test_native_own_memory_positive[65536]` — Windows AMD64 real requerido.
- `test_factory_abi_error_sanitized_before_resources` — Windows AMD64 real requerido.
- `test_poison_blocks_native_factory_before_binder` — Windows AMD64 real requerido.
- `test_native_backend_complete_abi` — Windows AMD64 real requerido.
- `test_invalid_width_rejects_before_dll` — Windows AMD64 real requerido.
- `test_missing_symbol_rejects_before_allocate` — Windows AMD64 real requerido.
- `test_closed_native_arguments_normalization[65536-2-None]` — Windows AMD64 real requerido.
- `test_closed_native_arguments_normalization[None-0-8]` — Windows AMD64 real requerido.

Sonda privada extra Linux, no incluida en 116: import protegido contra ctypes y factories originales rechazan `PLATFORM_UNSUPPORTED`, con cero intentos ctypes, sin DLL/alloc/calls. [Sonda](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/linux-inspected/private-linux-unsupported.json).

## Cobertura oficial de archivos completos

`coverage.py`, branch=True, sin omit, exclude_lines ni partial_branches. Combinación mediante `CoverageData.update(map_path=...)` de datos reales Windows/Linux inspeccionados, normalizando sólo rutas de esas dos fuentes SHA idénticas. No se sumaron porcentajes ni se omitió el binder. La ABI Linux sola queda por debajo de 80 %; Windows y la combinación real cubren ambos archivos individualmente por encima del umbral.

| Datos | Archivo completo | Líneas | Ramas cubiertas/total | Exclusiones |
|---|---|---:|---:|---:|
| windows-attempt2 | `storage_journal_windows_abi.py` | 70/70 (100.0000 %) | 10/10 | 0 |
| windows-attempt2 | `storage_journal_windows_io.py` | 370/376 (98.4043 %) | 100/108 | 0 |
| linux-inspected | `storage_journal_windows_abi.py` | 36/70 (51.4286 %) | 4/10 | 0 |
| linux-inspected | `storage_journal_windows_io.py` | 361/376 (96.0106 %) | 97/108 | 0 |
| combined | `storage_journal_windows_abi.py` | 70/70 (100.0000 %) | 10/10 | 0 |
| combined | `storage_journal_windows_io.py` | 370/376 (98.4043 %) | 100/108 | 0 |

[Detalle por plataforma y combinación](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/whole.json), [JSON oficial combinado](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/combined/coverage.json), [datos oficiales](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/combined/.coverage).

## Gates oficiales

Adaptador transparente de JUnit a resultados de qa-gate: conserva los 116 casos y outcomes, skips intactos; guarda SHA del JUnit en `results.json`. No es una ejecución Playwright ni E2E de la UI. Scripts oficiales, sin modificar.

Windows, exit 0:

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

Linux, exit 0:

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

`ledger-lint`: exit 0, 0 incoherencias, 1 aviso de UTF-8 del ledger original; no se corrigió. [Salida](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/ledger-lint.stdout).

`coverage-check`: exit 0, referencias rotas 0, aviso T-00 sin cobertura. Ledger/spec fijados y test-plan M1 vigente leído como contexto externo, sin editarlo. [Salida completa](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/coverage-check.stdout). El plan M1 **tiene UI**, sigue pendiente y no recibe exención global «sin UI» por esta prueba del componente.

`ruff check`: exit 0; [salida](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/ruff-check.stdout). `ruff format --check`: exit 1, 1 archivo requeriría formato (`tests/test_storage_journal_windows_io.py`, desde 839), 3 ya formateados; [diff de formato](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/ruff-format-check.stdout). No se editó ni ocultó.

## Diagnósticos e interrupciones propios

1. Windows intento1 abortó antes de resultados completos: la configuración privada se escribió inicialmente con BOM UTF-8; pytest no produjo datos y la exportación de cobertura abortó. El padre cerró por `CHILD_EARLY_EXIT` y perdió los streams de pipes; **no se recuperaron ni reconstruyeron**. Se conservan runner inicial, ready/CIM, `.coverage` incompleta y ausencia posterior de los dos PIDs. Intento2 corrigió sólo el harness y conservó streams.
2. Primer contenedor de inspección tuvo exit1 por comillas eliminadas en argv `python -c` de PowerShell. Se conserva inspect con argv exacto, wait1 y retirada; el stderr de su proceso no se capturó. No llegó a ejecutar los tests. El segundo contenedor usó un archivo wrapper propio y completó los 116 casos.
3. Primer extra privado de memoria falló en una aserción del harness que exigía eliminar el registro del contexto. El contrato conserva el registro cerrado para idempotencia; el test original no exigía eliminarlo. Se conserva traceback y CIM; ambos PIDs ausentes. La segunda sonda exige registro auténtico retenido y cerrado y pasa. No se alteró producto.
4. Búsqueda de herramienta PDF demasiado amplia interrumpida; no fue una prueba de producto.

## Pendientes manuales y estado de la cadena

- [ ] M-01/M-02/M-03 y E2E/API/UI integrales definidos en test-plan M1, fuera de esta auditoría.
- [ ] K2–K5, store, ACK, S1 full-chain, bootstrap/lifecycle, recuperación causal y ext4 reales.
- [ ] ROOT adjudica la conformidad de formato y decide adopción/CAS del componente; sin cierre de T-05/M1 ni handoff a documenter.

No se modificaron fuentes originales, tests, contratos, ledger, Git, locks, datos, instalaciones ni servicios. La evidencia del componente es local; no se publica en Confluence. Uso real de tokens/coste/horas IA: null. No se afirma durabilidad, aceptación del hito o ausencia universal de fugas.

## Addenda del harness y PDF

La reproducción privada collect-only confirma el error BOM original: exit4, `unexpected line: '\ufeff[pytest]'`; [stderr](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-k1-current-qa1-20261011/attempt1-bom-diagnostic.stderr). No recupera los streams perdidos del primer intento. La primera conversión PDF falló al buscar un Chrome no instalado en la caché predeterminada; la segunda usó Chromium existente dentro del proyecto y pasó, sin descargas.

La primera ejecución Ruff no desactivó su caché: pudo escribir dos entradas compartidas de `.ruff_cache/0.16.9` fuera del namespace de ownership. Se comunicó a ROOT y no se borró ni revirtió la caché concurrente. Los checks se repitieron con `--no-cache`, mismos resultados (check0/format1). Es un desvío del harness, no modificación de código, contratos o ledger.

La copia PDF y las previsualizaciones son artefactos privados de este namespace. La renderización local usa las dependencias existentes de `custom-agents:to-pdf`; ningún documento ni captura se envió a terceros.
