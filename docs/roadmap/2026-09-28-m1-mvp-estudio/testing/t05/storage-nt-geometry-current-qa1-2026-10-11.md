---
estado: DONE_WITH_CONCERNS
scope: M1T05/U2b2 geometría FIX1 componente CPU independiente
---

# QA independiente de geometría NT — 2026-10-11

El gate funcional del componente es VERDE. No certifica UI, E2E, T-05, M1, durabilidad ni aceptación del producto. No hay UI por el alcance de esta unidad; el test-plan global conserva sus E2E y manuales pendientes.

## Resultados nuevos

| Plataforma / suite | Pasan | Fallan | Omitidos | Deseleccionados |
|---|---:|---:|---:|---:|
| Windows suite exacta |419|0|0|0|
| Windows codec U1 |208|0|0|0|
| Linux CPU Docker real |301|0|29|89|

JUnit, streams, argv, cwd, UTC y salida terminal están en `evidence/windows/`, `evidence/codec/` y `linux-evidence/export/`. Los 29 skips y razones exactas están en `platform-skips.json`. Los 89 casos NT/transport de geometría fuera de selección Linux no equivalen a 419 ejecutados en Windows. No se instalaron dependencias ni se accedió a red, GPU, Ollama, servicios ajenos o datos de producto.

## Gate determinista real

La adaptación `results-adapted.json` convierte cada testcase JUnit real a un resultado para qa-gate; no inventa ejecución Playwright ni E2E. No hay reintentos o flaky justificados.

```json
{

  "verdict": "VERDE",

  "counts": {

    "passed": 928,

    "failed": 0,

    "flaky": 0,

    "skipped": 29,

    "interrupted": 0

  },

  "flaky_sin_justificar": [],

  "flaky_justificados": {},

  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"

}

```

## Cobertura oficial de módulos completos

| Suite / módulo | Líneas | Ramas | Excluidas |
|---|---:|---:|---:|
|windows|90.41095890%|89.06250000%|0|
|codec|95.00000000%|90.55944056%|0|
|linux|73.69863014%|67.18750000%|0|

Windows runtime y codec superan 80% de líneas y ramas sin omit/exclude. Linux mide el subconjunto portable; su módulo completo queda debajo del 80%, documentado y sin atribuir una unión no realizada. JSON oficiales completos: `windows-coverage.json`, `codec-coverage.json`, `linux-evidence/export/coverage.json`. Gate de cobertura: `coverage-component-gate.json`.

## Observaciones nativas y custodia

`own-probes.json` acredita cuatro testigos NT propios adicionales (dos archivos y dos directorios), ambas queries reales con status0/IOSB0/information28/4/raw/metadata de la misma adquisición. B es diagnóstico, no admisión. Dos probes PENDING propios usan dobles en hijos: retienen composite/owner, bloquean otro contexto, close unknown repetido sin syscall y padre termina/wait/reap antes de retornar. No se observó PENDING nativo.

La suite conserva R01–R21: argumentos/ABI, errores, completion, lengths, transferencia, PENDING, retención, identidad, tamaños, masks, flags, offsets, frozen DTO, no ampliación, NT ordinario y portabilidad. Los escenarios tienen sus testcases en JUnit; la prueba de custodia no sustituye powerloss/store/ACK.

`children-verified.json` verifica todos los recibos presentes, incluidos geometry-child/fix1-child y child-reap U2b1; streams por SHA donde el recibo lo aporta. Reparse points inventariados por lstat sin seguimiento. No se reutilizan resultados de implementación/revisión: `mechanics-receipt.json` traza únicamente las mecánicas copiadas y el parser real receipt fijado 811a578.

## Integridad y entorno

Importaciones exactas y SHA por archivo: `evidence/windows/imports.json`, `evidence/codec/imports.json`, `linux-evidence/export/imports.json`, `own-probes.json`. Runtime privado8f0e7bd/tests145a883; canonaf192/3de1e82 preservado en guardas before/after. Los27sources permanecen byte exactos. Ruff check/format y ledger-lint snapshot exit0 con stdout/stderr/receipts independientes. Ledger-lint informa 0 incoherencias y 1 aviso: fichero no UTF-8 limpio (leído con reemplazos). El aviso se conserva; QA no recodifica el ledger.

Docker usa imagen fijada7c65be72, UID10001, readonly rootfs/mounts, networknone, capdropALL, no-new-privileges. `linux-evidence/commands.json` registra creación propia, export TAR después del terminal del runner, hash/bytes/miembros regulares verificados antes de retirar, wait del contenedor, inspect PID0 y rm; `cleanup.json` acredita retirada. FFmpeg/audio/render no aplican a este componente.

## Pendientes manuales e integrales

- [ ] G2 cadena S1/bootstrap y adquisición writer propia.
- [ ] Store/writer/ACK/crash/lifecycle y ext4 persistente reales.
- [ ] E2E y manuales globales M1, incluida aceptación musical.
- [ ] ROOT verifica esta entrega y decide CAS acotado; QA no modifica canon, ledger, Git ni estados.

El plan y T05 permanecen abiertos. No hay handoff documental de cierre de hito. Esta entrega prueba exclusivamente el componente readonly bajo el contrato ADR0078 §4.1–4.6/R01–R21.


## Verificación e incorporación de ROOT

ROOT 2026-10-11T14:06:03.528523+00:00: manifiesto769artefactos, fuentes27, imports Windows/codec/Linux, JUnit419/208/301+29skip,100recibos de hijos,4testigos NT,154miembros TAR y retirada del contenedor propio verificados. Revisión de producto2 A/B sin gaps; cuatro Important previos corregidos. Sólo se incorporan runtime y tests examinados; codec/parser permanecen intactos. Windows runtime supera80% de líneas/ramas; Linux portable permanece medido por separado debajo80%.

El PDF original conserva el informe independiente (3páginas); comprobación estructural y preview print inspeccionado, sin rasterización del PDF. La salida literal del gate contiene una cadena explicativa con mojibake; sus counts y verdict están verificados, sin atribuir la corrupción a un fallo funcional.

Componente readonly aceptado; T05/M1 siguen en progreso. Bootstrap/S1 completo, store/writer/ACK/crash/lifecycle, ext4 persistente, E2E y manuales son pendientes obligatorios.
