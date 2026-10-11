# QA independiente — contrato documental K4a Windows

**VERDE documental: 232/232 comprobaciones, 0 fallos, 0 flaky. T05/M1 permanecen abiertos.**

Fuente privada actual `3c20d078f3d71bee6bafe7089c8028c83e315313eb0f2380e5ee8bdd236cc51e`, 70176 bytes, 515 líneas; diff de cinco documentos. ADR-0084 permanece propuesta privada. ROOT audita y adopta posteriormente; esta QA no modifica ledger, CAS, Git ni fuentes. Uso real (tokens/euros/horas IA): null.

## Alcance y resultado

Se verificaron 41 pins snapshot y 39 guardas canónicas, más dos ausencias canónicas, antes y después. Los recibos ROOT, opción O1, revisiones anteriores y fusión completa A44/B18 se conservan. La ejecución Python de controles es prosa/AST: cero imports de runtime, llamadas backend o queries nativas. No se ejecutaron UI, servicios, WSL, GPU, ACL ni operaciones administrativas.

| Comprobación | Resultado y evidencia |
|---|---|
| Corrección B01 | Prefijo real K1 extraído por AST: 131328/8 y 131328/512 rechazan ALIGNMENT_INVALID; 131584/512 solicita 132095. Sin invocar el allocator completo ni backend. |
| Bordes K1 | bool rechaza INTEGER_INVALID; count8, sum(n)+1 y sum(r)+1 rechazan ARENA_LIMIT; size_t132094 rechaza OVERFLOW,132095 pasa. |
| SDK y backing | L131328, n131584, B512, r132095, tail256/margen511. Bases4096/4097 verificadas aritméticamente, no son direcciones obtenidas de una allocation real. |
| Queries y ReturnLength | Dos ventanas65536, bounds de SID completos dentro del ReturnLength de su ventana; tail/padding/otra ventana no amplían salida. Struct SDK alignment8 distinto de allocator512. |
| Fuentes SDK | 12 pins históricos y sección fijada a commit656e9656 intactos respecto a fuente24deb33e. Firmas/layouts son contrato deducido documentalmente; no acreditan SDK instalado o ABI nativa probada. Sin red/fetch nuevos. |
| Accounting/custodia | Payload solicitado394887=132095+262656+136; un backing. Unknown retiene carga y custodia; close/free reconocidos una vez; cuts postTRUE no autorizan retry ni cleanup hermano. |
| Interop | Prefijos C2/K2 íntegros byte exactos; coordinación extraída byte exacta: boundary→owner→session→context, registry breve/suelto antesRLock, pin con owner ya held sin lock tardío; mismo poison. |
| Autoridad O1 | Factory privada sin inputs autoritativos, controller confiable S1 y PID/thread/token propios, policy/epoch nominales finitas; SID/path/flag/DTO no conceden autoridad. |
| Separación futura | CREATE exige guard K4b/fullS1; K5 cerrado; RootContext posterior. K1 actual carece del nuevo preludio de coordinación: su implementación y QA whole actual/native continúan pendientes. |

## Puertas deterministas

`ledger-lint.py`: exit0, 0 incoherencias y dos avisos históricos preservados (UTF8 reemplazado, cabecera revisión línea5281). `coverage-check.py`: exit0, 0 referencias rotas y 0 GWT huérfanos. El aviso T-00 es documental (`Tipo: docs`, secuenciación), no UI. Ninguno de estos resultados ejecuta los E2E de producto M1. La cobertura whole≥80 de módulos futuros no se mide ni se inventa en esta QA de prosa.

Salida íntegra real de `qa-gate.py` sobre los controles documentales actuales:

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 232,
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

## Evidencias y trazabilidad

T05→K4a contractual→checks.json/results.json→qa-gate.stdout. Snapshot y guardas→before-guards.json/after-guards.json. Cada comprobación tiene resultado y detalle en checks.json; los recibos por comando incluyen argv, cwd, UTC, exit, stdout/stderr y SHA de fuente actual. Esta suite no se presenta como Playwright ni como E2E. El gate consume su representación JSON compatible, con resultados reales derivados de las comprobaciones.

PDF propio `evidence/report.pdf`, generado con skill to-pdf adaptada para resolución de módulos locales, Chromium instalado y perfil propio. Inspección visual disponible: capturas first/last del HTML en modo impresión; **páginas del PDF no rasterizadas**. Esta limitación no se reemplaza por una afirmación de inspección raster. El cierre del browser propio y su PID se registra por renderer; no es el reap futuro del controller K4a.

## Checklist pendiente de producto

- [ ] K4a-01…18: implementación TDD y QA CPU/nativa propia actual; queries de token y ctypes/layouts reales Windows, PID propio y reap acreditados tras release ROOT.
- [ ] Regresión whole≥80 sin exclusiones de módulos K1/K2/K4a modificados, nueva coordinación/poison y supervisor de retirada.
- [ ] K3/K4b/K5/G1 y full-chain S1 positivo; host MODIFY outsider sigue sin remediar.
- [ ] Store/ACK/recovery/bootstrap/lifecycle/ext4 persistente y E2E completos.
- [ ] M-01 generación real GPU y escucha; M-02 revisión visual/accesibilidad; M-03 backup/restauración.

No se cierran plan/spec ni tareas y no se entrega documentación de producto como implementado. ROOT conserva la adopción documental final y todas las puertas pendientes.

## Índice completo de controles

| Control | Resultado | Detalle |
|---|---|---|
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\pyproject.toml | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-durable-design.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-nt-geometry-design.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\tasks.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-kernel-design.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0041-esquema-inicial-y-snapshots-del-server.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\.claude\dev.json | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\spec.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\tests\test_storage_journal_windows.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_attach.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_journal_windows.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\tests\test_storage_journal_windows_abi.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_offline.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-nt-security-policy.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_operator.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\uv.lock | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-principal-design.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\improvement-plan.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_windows.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_receipt_store.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_journal_windows_abi.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\README.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\packages\storage-guard\studio_storage_guard\receipt.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\env.ps1 | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-store-design.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_publish.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\AGENTS.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\tests\conftest.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\tests\test_storage_journal_windows_io.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_journal_windows_io.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\testing\t05\storage-journal-store-flush-native-2026-10-11.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\.cache\dev-cycle\m1\storage-journal-store-flush-probe-20261011\flush_probe_experimental.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0084-frontera-nativa-y-admision-del-principal-windows.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_journal.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\CONSTITUTION.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\conftest.py | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-acquisition-design.md | PASS |  |
| before pin .cache\dev-cycle\m1\storage-journal-store-flush-probe-20261011\flush_probe_experimental.py | PASS |  |
| before pin .claude\dev.json | PASS |  |
| before pin AGENTS.md | PASS |  |
| before pin conftest.py | PASS |  |
| before pin docs\CONSTITUTION.md | PASS |  |
| before pin docs\decisiones\ADR-0041-esquema-inicial-y-snapshots-del-server.md | PASS |  |
| before pin docs\decisiones\ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md | PASS |  |
| before pin docs\decisiones\ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md | PASS |  |
| before pin docs\decisiones\ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | PASS |  |
| before pin docs\decisiones\README.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\improvement-plan.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\spec.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-durable-design.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-acquisition-design.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-kernel-design.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-store-design.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-nt-geometry-design.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-nt-security-policy.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\tasks.md | PASS |  |
| before pin docs\roadmap\2026-09-28-m1-mvp-estudio\testing\t05\storage-journal-store-flush-native-2026-10-11.md | PASS |  |
| before pin packages\storage-guard\studio_storage_guard\receipt.py | PASS |  |
| before pin pyproject.toml | PASS |  |
| before pin scripts\env.ps1 | PASS |  |
| before pin scripts\storage.py | PASS |  |
| before pin scripts\storage_attach.py | PASS |  |
| before pin scripts\storage_journal.py | PASS |  |
| before pin scripts\storage_journal_windows.py | PASS |  |
| before pin scripts\storage_journal_windows_abi.py | PASS |  |
| before pin scripts\storage_journal_windows_io.py | PASS |  |
| before pin scripts\storage_offline.py | PASS |  |
| before pin scripts\storage_operator.py | PASS |  |
| before pin scripts\storage_publish.py | PASS |  |
| before pin scripts\storage_receipt_store.py | PASS |  |
| before pin scripts\storage_windows.py | PASS |  |
| before pin tests\conftest.py | PASS |  |
| before pin tests\test_storage_journal_windows.py | PASS |  |
| before pin tests\test_storage_journal_windows_abi.py | PASS |  |
| before pin tests\test_storage_journal_windows_io.py | PASS |  |
| before pin uv.lock | PASS |  |
| before absent docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-principal-design.md | PASS |  |
| before absent docs/decisiones/ADR-0084-frontera-nativa-y-admision-del-principal-windows.md | PASS |  |
| input prepare-root.receipt.json | PASS | 719f08e5cf16ddd5eed4bfefab54703d2f06cbbbb75eb45f9e9989b5b660915e |
| input prior-review.md | PASS | c86ac9e8d66a9dce2bc8ddd4ed5f2e0ad463b2d1514b89161d26bebc59de3298 |
| input verdict-transfer-root.md | PASS | 4923e73875640140266bbf0b59de0e044e6b265a99d2de93bdb80fcd11dae57a |
| input options-preserved-root.md | PASS | d2d0e6841bb0035540939949097d3e386cdd5ac8ae0ae550146e9ec4703c8e68 |
| input choice-root.receipt.json | PASS | be6905a3691d142b61fb908b180e82e30629f212c86258d87f86242d1b770171 |
| input source.diff | PASS | b86597665cb93a6b63bbfc408c86b81ae02799af103c6809e0bccb1b2dba88f1 |
| O1 selection | PASS |  |
| source exact bytes/lines | PASS | (70176, 515) |
| five documentary paths | PASS |  |
| canonical historical prefix storage-journal-kernel-design.md | PASS |  |
| coordination extraction byte exact storage-journal-kernel-design.md | PASS |  |
| canonical historical prefix storage-journal-acquisition-design.md | PASS |  |
| coordination extraction byte exact storage-journal-acquisition-design.md | PASS |  |
| 12 historical SDK pins | PASS |  |
| historical source located | PASS |  |
| SDK pinned section unchanged | PASS |  |
| actual K1 AST (131328, 8, (0, 0, 0)) | PASS | 'ALIGNMENT_INVALID' |
| actual K1 AST (131328, 512, (0, 0, 0)) | PASS | 'ALIGNMENT_INVALID' |
| actual K1 AST (131584, 512, (0, 0, 0)) | PASS | 132095 |
| actual K1 AST (True, 512, (0, 0, 0)) | PASS | 'INTEGER_INVALID' |
| actual K1 AST (131584, 512, (8, 0, 0)) | PASS | 'ARENA_LIMIT' |
| actual K1 AST (131584, 512, (0, 8781313, 0)) | PASS | 'ARENA_LIMIT' |
| actual K1 AST (131584, 512, (0, 0, 9305082)) | PASS | 'ARENA_LIMIT' |
| actual K1 size_t edge 132094 | PASS | 'OVERFLOW' |
| actual K1 size_t edge 132095 | PASS | 132095 |
| no native boundary prelude in current K1 | PASS |  |
| arith aligned base 4096 | PASS | {'a': 4096, 'sdk_end': 135424, 'arena_end': 135680, 'backing_end': 136191} |
| arith aligned base 4097 | PASS | {'a': 4608, 'sdk_end': 135936, 'arena_end': 136192, 'backing_end': 136192} |
| one backing payload accounting | PASS |  |
| SDK bounds retained 256..65791 | PASS |  |
| SDK bounds retained 65792..131327 | PASS |  |
| SDK bounds retained capacity<=65536 | PASS |  |
| SDK bounds retained [base,base+ReturnLength) | PASS |  |
| SDK bounds retained tail256 no se inicializa | PASS |  |
| struct layouts distinct TOKEN_STATISTICS  /  56/8 | PASS |  |
| struct layouts distinct ModifiedId48 | PASS |  |
| struct layouts distinct TOKEN_PRIMARY_GROUP  /  8/8 | PASS |  |
| struct layouts distinct alineación8 de structs/slots SDK es independiente de B512 | PASS |  |
| private finite controller authority _bootstrap_current_deployer() -> _DeployerAuthority | PASS |  |
| private finite controller authority sin argumentos | PASS |  |
| private finite controller authority No hay parámetro `trusted` | PASS |  |
| private finite controller authority TOKEN_QUERY=8 | PASS |  |
| private finite controller authority policy S1 immutable | PASS |  |
| private finite controller authority PID/thread_ref/thread_id | PASS |  |
| pin owner lock/order owner ya bloqueado | PASS |  |
| pin owner lock/order No toma boundary ni owner después | PASS |  |
| pin owner lock/order siempre se suelta antes de esperar un RLock | PASS |  |
| pin owner lock/order owner K2.RLock, si existe → session K4a.RLock → context K1.RLock | PASS |  |
| custody cuts and free once close native attempts<=1 | PASS |  |
| custody cuts and free once El primer close unknown detiene cleanup restante | PASS |  |
| custody cuts and free once sin free ni decremento adicional | PASS |  |
| custody cuts and free once Unknown conserva toda la carga y custodia | PASS |  |
| custody cuts and free once sumarla otra vez | PASS |  |
| future authority separate _ParentS1Admission | PASS |  |
| future authority separate CREATE sigue exigiendo guard | PASS |  |
| future authority separate OWNED_PROBE_CANDIDATE | PASS |  |
| future authority separate K4a no emite | PASS |  |
| future authority separate Coverage80 whole | PASS |  |
| future authority separate terminate/reap real | PASS |  |
| quotas finite 2048 / 1 | PASS |  |
| quotas finite 8192 | PASS |  |
| quotas finite 229376=8192*28 | PASS |  |
| quotas finite Admissions lifetime  /  4 | PASS |  |
| quotas finite Threads observados lifetime  /  8 | PASS |  |
| quotas finite 9437176 | PASS |  |
| ADR84 remains private proposal | PASS |  |
| ledger lint exit zero | PASS |  |
| coverage-check exit zero | PASS | M1 gate is traceability, not execution of product E2E |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\pyproject.toml | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-durable-design.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-nt-geometry-design.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\tasks.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-kernel-design.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0041-esquema-inicial-y-snapshots-del-server.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\.claude\dev.json | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\spec.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\tests\test_storage_journal_windows.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_attach.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_journal_windows.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\tests\test_storage_journal_windows_abi.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_offline.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-nt-security-policy.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_operator.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\uv.lock | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-principal-design.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\improvement-plan.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_windows.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_receipt_store.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_journal_windows_abi.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\README.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\packages\storage-guard\studio_storage_guard\receipt.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\env.ps1 | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-store-design.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_publish.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\AGENTS.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\tests\conftest.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\tests\test_storage_journal_windows_io.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_journal_windows_io.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\testing\t05\storage-journal-store-flush-native-2026-10-11.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\.cache\dev-cycle\m1\storage-journal-store-flush-probe-20261011\flush_probe_experimental.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\decisiones\ADR-0084-frontera-nativa-y-admision-del-principal-windows.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\scripts\storage_journal.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\CONSTITUTION.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\conftest.py | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-principal-k4a-contract-current-qa1-20261011\snapshot\docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-acquisition-design.md | PASS |  |
| after pin .cache\dev-cycle\m1\storage-journal-store-flush-probe-20261011\flush_probe_experimental.py | PASS |  |
| after pin .claude\dev.json | PASS |  |
| after pin AGENTS.md | PASS |  |
| after pin conftest.py | PASS |  |
| after pin docs\CONSTITUTION.md | PASS |  |
| after pin docs\decisiones\ADR-0041-esquema-inicial-y-snapshots-del-server.md | PASS |  |
| after pin docs\decisiones\ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md | PASS |  |
| after pin docs\decisiones\ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md | PASS |  |
| after pin docs\decisiones\ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | PASS |  |
| after pin docs\decisiones\README.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\improvement-plan.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\spec.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-durable-design.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-acquisition-design.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-kernel-design.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-journal-store-design.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-nt-geometry-design.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\storage-nt-security-policy.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\tasks.md | PASS |  |
| after pin docs\roadmap\2026-09-28-m1-mvp-estudio\testing\t05\storage-journal-store-flush-native-2026-10-11.md | PASS |  |
| after pin packages\storage-guard\studio_storage_guard\receipt.py | PASS |  |
| after pin pyproject.toml | PASS |  |
| after pin scripts\env.ps1 | PASS |  |
| after pin scripts\storage.py | PASS |  |
| after pin scripts\storage_attach.py | PASS |  |
| after pin scripts\storage_journal.py | PASS |  |
| after pin scripts\storage_journal_windows.py | PASS |  |
| after pin scripts\storage_journal_windows_abi.py | PASS |  |
| after pin scripts\storage_journal_windows_io.py | PASS |  |
| after pin scripts\storage_offline.py | PASS |  |
| after pin scripts\storage_operator.py | PASS |  |
| after pin scripts\storage_publish.py | PASS |  |
| after pin scripts\storage_receipt_store.py | PASS |  |
| after pin scripts\storage_windows.py | PASS |  |
| after pin tests\conftest.py | PASS |  |
| after pin tests\test_storage_journal_windows.py | PASS |  |
| after pin tests\test_storage_journal_windows_abi.py | PASS |  |
| after pin tests\test_storage_journal_windows_io.py | PASS |  |
| after pin uv.lock | PASS |  |
| after absent docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-principal-design.md | PASS |  |
| after absent docs/decisiones/ADR-0084-frontera-nativa-y-admision-del-principal-windows.md | PASS |  |
