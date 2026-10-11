# QA2 documental independiente — contrato pre-RED K1 FIX1

Estado: **VERDE documental**, 91/91 controles individuales; 0 fallos. El gate oficial terminó 0. No constituye aceptación K1, T05 o M1 ni release de implementación.

Fuente kernel SHA-256: `7ceae414e61d18f5821df1c55bef1e130ffdcd72612dfb5d09f222423cd6f839`. Snapshot18 fijado por [release ROOT](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/release-root.receipt.json); [controles individuales](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/individual-checks.json), [JUnit](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/documentary.junit.xml), [adaptación documental JSON](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/adapted-documentary-results.json), [recibo gate](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/qa-gate.receipt.json), [guards antes](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/guards-before.json)/[después](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/guards-after.json).

## Veredicto determinista oficial

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 91,
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

## QA1-01 y cuotas

FIX1 define `quota_accounting=requested_bytes_including_padding`, `r=n+B-1`, count8, `sum(n)<=8912896` y `sum(r)<=9437176`. Admisión registra `(1,n,r)` antes de entered bajo RLock; NULL acreditado/TRUE completamente reconocido devuelven esa carga exacta. Uncertain mantiene cuotas y revoca autoridad, sin retry. La cuota mide lo solicitado al backend; no memoria OS o física.

Control aritmético propio: n1114112/B65536 → r1179647; ocho solicitudes9437176. Con página4096 **supuesto**, redondeo1179648×8=9437184, ocho bytes más. No ejecución VirtualAlloc, medición OS, reserva física ni autoridad native por esta aritmética. [Resultados nuevos](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/accounting-arithmetic.json). QA1 real66PASS1FAIL/gateexit1 preservada byte exacta; no se reutiliza como verde para SHA7ceae414.

## Alcance y límites

Se comprueban las dos propuestas documentales C2/O2, ADR0081, 12 criterios K1, API/DTO/policy, referencias y obligaciones completas. Enlaces resueltos desde el destino canónico, con snapshot fijado primero y fallback actual sólo para referencias readonly autorizadas; [inventario](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/links.json). Revisión2 fusionada ROOT conserva tablas actuales y respuestas históricas; no se presenta como ejecución propia.

Diagnósticos propios preservados en [diagnostic1](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/diagnostic1/report.md): auditor inicial87PASS2FAIL/gate1 por literal `no un` frente a `ni un` y campo `exit_code` frente al histórico `exit`. Corregidos sólo en auditor y ejecutado de nuevo; sin edición fuente. También se conserva la preimagen del auditor anterior al soporte BOM del manifest histórico; fallo de preparación inicial JSONDecodeError, antes de evaluar casos. No son fallos de producto ni flaky justificados. GOT-001 consultado como **propuesta no validada** sobre bind/rename; no condiciona esta pasada de memoria documental y no se escribe gotcha.

Ledger-lint oficial: exit0, `0 incoherencias`, **1 aviso UTF8 histórico** conservado sin reescritura; [salida](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/ledger.stdout), [recibo](../../../../../.cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-20261011/ledger.receipt.json). Coverage-check E2E global no se ejecuta en esta unidad documental: no se liberó UI/test-plan K1. La cobertura K1-01..12 se documenta abajo; no acredita cobertura del producto M1. TDD y coverage changed-runtime: n/a prosa. Whole>=80% por cada uno de los dos módulos futuros, ramas, Linux negativo y Windows real siguen pendientes. No pytest global, navegador, UI/E2E, archivo nativo, GPU/Ollama, admin/ACL, SQLite, Git ni servicio ejecutados. Guardrail local: ninguna URL/host fue objetivo de QA; sin conexión de prueba a terceros. PDF omitido expresamente en este scope documental autorizado.

## Resultados individuales y trazabilidad T05/K1

Cada fila corresponde a una evaluación nueva registrada con UTC, resultado y expectativa, no un número de casos elegido de antemano. El JSON adaptado sólo nombra controles documentales; el gate no los transforma en tests runtime.

| Control | Resultado | Expectativa comprobada |
|---|---|---|
| PIN scripts/storage_journal_windows.py | PASS | 8f0e7bdb4c5dda0b92d186ea8293861209efe9170e5c36d8ce21c7662395c973 |
| PIN packages/storage-guard/studio_storage_guard/receipt.py | PASS | 811a5782ab0b84c0252e552e871d976fd944ec8059591c9afc492370394846f5 |
| PIN .cache/dev-cycle/m1/storage-journal-store-flush-probe-20261011/flush_probe_experimental.py | PASS | 087288e3c20f21877cdbbc624fa0e332d3a765134e1fef4b84c0f093308d3bf9 |
| PIN .claude/dev.json | PASS | ee4728bbc6a88539c5f85c2050dcd1c1bea9ece58e93f5fafa4f2d497c2b70b1 |
| PIN docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md | PASS | 15b555c14bc54731223b914914e2a82a9b4d5138b945981f76aac2a5c85729a0 |
| PIN docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md | PASS | 4b87e0f36d1e05b05a3274876006aabf7b5a8e7f1cee4208c80321d99c7acdab |
| PIN docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md | PASS | 489f7521786574c554e8a276cf1eeca68fad557b5aed6e9c9132d0338953eefa |
| PIN AGENTS.md | PASS | 914438ce2743d757d6b0aca903cafb6abd7e5075676ae35ee6bb82b71a328789 |
| PIN docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md | PASS | 7ab1bb1ec9b4c65b901ac2c1f73c493048482fdc0802098c35f5237b4dbf89b9 |
| PIN docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | PASS | 71a54e543c589d41f255445b08daaaeeabb7a6b5745db2ae6b9e5175add581a8 |
| PIN docs/CONSTITUTION.md | PASS | b15df6b30747dbe594d97a8fe2f896509586da4b890de981c42c1f27234861b2 |
| PIN tests/test_storage_journal_windows.py | PASS | 145a8832b79aaa673b64b637a22ad42c37e4e437c2c636a4835cb8d302ba690f |
| PIN docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md | PASS | 10fadd0c88b44b42778a739335204267664a3a94beb37620b34719d02fd034d6 |
| PIN docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-journal-store-flush-native-2026-10-11.md | PASS | beebed7aeff53b5fe1ffe4d347a1d2e96aa516f994f358c29ff572a554ec5a5c |
| PIN docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md | PASS | 47abeb0ccece79e7927e212f3a279df593c445675690a94577e2e73d83a80122 |
| PIN scripts/storage_journal.py | PASS | 5db83df2584f419177162054c02eda46c33abcca253bcf3b2130301bec6f6ea5 |
| PIN docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md | PASS | 7ceae414e61d18f5821df1c55bef1e130ffdcd72612dfb5d09f222423cd6f839 |
| PIN docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md | PASS | b71f4940a6c297de922e5b63bf7a12567b2bdc139ee649ca7045e11cb2471eab |
| review2 receipt pin | PASS | f721805f1875c43586d237a6ceb1f152e986645f305374c346c20717bf9c7a81 |
| review2 verdict transfer pin | PASS | 894aec399bd29c32cd8abee68dd89a0efa5df37233df9fe840fb057637eb7925 |
| review2 snapshot pins match QA2 | PASS | {'scripts/storage_journal_windows.py': '8f0e7bdb4c5dda0b92d186ea8293861209efe9170e5c36d8ce21c7662395c973', 'packages/storage-guard/studio_storage_guard/receipt.py': '811a5782ab0b84c0252e552e871d976fd944ec8059591c9afc492370394846f5', '.cache/dev-cycle/m1/storage-journal-store-flush-probe-20261011/flush_probe_experimental.py': '087288e3c20f21877cdbbc624fa0e332d3a765134e1fef4b84c0f093308d3bf9', '.claude/dev.json': 'ee4728bbc6a88539c5f85c2050dcd1c1bea9ece58e93f5fafa4f2d497c2b70b1', 'docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md': '15b555c14bc54731223b914914e2a82a9b4d5138b945981f76aac2a5c85729a0', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md': '4b87e0f36d1e05b05a3274876006aabf7b5a8e7f1cee4208c80321d99c7acdab', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md': '489f7521786574c554e8a276cf1eeca68fad557b5aed6e9c9132d0338953eefa', 'AGENTS.md': '914438ce2743d757d6b0aca903cafb6abd7e5075676ae35ee6bb82b71a328789', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md': '7ab1bb1ec9b4c65b901ac2c1f73c493048482fdc0802098c35f5237b4dbf89b9', 'docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md': '71a54e543c589d41f255445b08daaaeeabb7a6b5745db2ae6b9e5175add581a8', 'docs/CONSTITUTION.md': 'b15df6b30747dbe594d97a8fe2f896509586da4b890de981c42c1f27234861b2', 'tests/test_storage_journal_windows.py': '145a8832b79aaa673b64b637a22ad42c37e4e437c2c636a4835cb8d302ba690f', 'docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md': '10fadd0c88b44b42778a739335204267664a3a94beb37620b34719d02fd034d6', 'docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-journal-store-flush-native-2026-10-11.md': 'beebed7aeff53b5fe1ffe4d347a1d2e96aa516f994f358c29ff572a554ec5a5c', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md': '47abeb0ccece79e7927e212f3a279df593c445675690a94577e2e73d83a80122', 'scripts/storage_journal.py': '5db83df2584f419177162054c02eda46c33abcca253bcf3b2130301bec6f6ea5', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md': '7ceae414e61d18f5821df1c55bef1e130ffdcd72612dfb5d09f222423cd6f839', 'docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md': 'b71f4940a6c297de922e5b63bf7a12567b2bdc139ee649ca7045e11cb2471eab'} |
| review2 full diff hash | PASS | 3a93a30be14bdc1ed4b6392b72c298f749e7cad20f7bd6d02a3a9577ae8259ba |
| review2 FIX1-only diff hash | PASS | 7a39878164f6ae4a39299a3736cb1a27068012996ae6bd76759e776a881d817f |
| scope two documentary destinations only | PASS | kernel design and parent design |
| C2 selected, not adopted or released | PASS | ['opcion_elegida: C2', 'canonical_adopted: false', 'implementation_released: false', 'actual_usage: null', 'C1 se descarta'] |
| parent O2 and ADR0081 unchanged authority | PASS | ['opcion_elegida: O2', 'storage-journal-kernel-design.md', 'No sustituye el store O2'] |
| ADR0081 kernel/store decision retained | PASS | ['opcion: O2', 'estado: aceptada', 'RootContext/ChainLease nacen sólo', 'Bootstrap legacy, lifecycle', 'ext4/UUID'] |
| K1-01 future conformance documentary | PASS | ['os.name', 'sys.platform', 'ARM64/32bits', 'antes de ctypes/DLLs'] |
| K1-02 future conformance documentary | PASS | ['tamaño16/alineación8', 'tamaño48/alineación8', 'Information:size_t@8', 'argtypes/restype', 'ABI_UNACCREDITED'] |
| K1-03 future conformance documentary | PASS | ['MAX_ARENA_BYTES=1048576+65536=1114112', 'r=n+B-1', 'base+r<=SIZE_T_MAX', 'a+n<=base+r', 'offset<=n', 'sin redondeo OS'] |
| K1-04 future conformance documentary | PASS | ['type(x) is ExpectedType', 'pertenencia al registro', 'object.__new__', 'No existen `RootContext`'] |
| K1-05 future conformance documentary | PASS | ['bytes exactos', 'bytes nuevos independientes', 'Copia vacía válida', 'length<=n-offset'] |
| K1-06 future conformance documentary | PASS | ['context.inflight', 'preinsertado', 'aunque el retorno no haya llegado a guardarse'] |
| K1-07 future conformance documentary | PASS | ['Reservar CloseOutcome unknown', 'marcar revoked', 'backend-call count total<=1', 'jamás retry'] |
| K1-08 future conformance documentary | PASS | ['orden inverso', 'Si un cierre falla', 'causa primaria', 'devuelve carga registrada `(1,n,r)`'] |
| K1-09 future conformance documentary | PASS | ['context.RLock', 'Ningún camino mantiene guardia global esperando un RLock', 'pid actual', 'GIL no es un lock'] |
| K1-10 future conformance documentary | PASS | ['DTO frozen', 'No usa `str(error)`', 'suprime chaining público', 'FailureDiagnostic.ntstatus'] |
| K1-11 future conformance documentary | PASS | ['Windows nativo liberado aparte por ROOT', 'sin NtCreateFile, flush, GPU/admin/ACL/archivo', 'No se convierte skip native en pass'] |
| K1-12 future conformance documentary | PASS | ['whole>=80% por archivo nuevo', 'Cada uno alcanza >=80%', 'No se maquilla un archivo por el promedio', 'sin omit/exclude/pragmas'] |
| closed facade _new_memory_context() | PASS | ['_new_memory_context()'] |
| closed facade _allocate_aligned(context | PASS | ['_allocate_aligned(context'] |
| closed facade _arena_info(context | PASS | ['_arena_info(context'] |
| closed facade _arena_copy_in(context | PASS | ['_arena_copy_in(context'] |
| closed facade _arena_copy_out(context | PASS | ['_arena_copy_out(context'] |
| closed facade _close_arena(context | PASS | ['_close_arena(context'] |
| closed facade _close_memory_context(context | PASS | ['_close_memory_context(context'] |
| six internal DTOs frozen and closed | PASS | ['ArenaInfo(length:int, alignment:int, state:str, provenance:str)', 'CloseOutcome(state:str, causes:tuple[FailureDiagnostic,...])', 'FailureDiagnostic(code:str, operation:str, win32_error:int-or-None, ntstatus:int-or-None)', '_AllocResult(base:int-or-None, win32_error:int-or-None)', '_BoolResult(success:bool, win32_error:int-or-None)', '_MemoryOps(allocate, release, copy_in, copy_out)'] |
| assembly private and CPU double cannot confer writer | PASS | ['_assemble_memory_context(ops: _MemoryOps, *, provenance: str)', 'tests entran por assembly privada con `cpu_double`', 'nunca genera writer', 'No aceptará `_MemoryContext` como RootContext'] |
| native memory-only binding | PASS | ['MEM_RESERVE/MEM_COMMIT=0x3000', 'PAGE_READWRITE=0x4', 'MEM_RELEASE=0x8000', 'base original, size0', 'K1 invoca sólo alloc/free/copias', 'ni un calling seam arbitrario'] |
| global poison retains uncertain ownership | PASS | ['_KERNEL_POISONED', '_QUARANTINED_MEMORY_CONTEXTS', 'No recupera cuotas uncertain', 'No comparte ni restablece los globals de U2', 'Un supervisor confiable tendrá que terminar/reap'] |
| closed diagnostics and no authority leaks | PASS | ['PLATFORM_UNSUPPORTED', 'ABI_UNACCREDITED', 'CAPABILITY_INVALID / CAPABILITY_REVOKED / OWNER_MISMATCH', 'INTEGER_INVALID / RANGE_INVALID / ALIGNMENT_INVALID / OVERFLOW / ARENA_LIMIT', 'ALLOCATION_FAILED', 'RESOURCE_UNKNOWN / OWNER_RETIRE_REQUIRED', 'sin address/base/pid reutilizable', 'No destructor, atexit, finalizer'] |
| quota accounting precise and physical distinction | PASS | ['quota_accounting: requested_bytes_including_padding', 'El total lógico es `sum(n)`', 'La cuota solicitada es `sum(r)`', 'arena_count<8', 'n<=8912896-logical_bytes', 'r<=9437176-requested_bytes', 'carga provisional `(1,n,r)`', 'nunca sustituye `r` por un tamaño redondeado', 'Página4096 es un supuesto aritmético', 'El limiter sigue usando `sum(r)`', 'no fija una cota física'] |
| rollback known NULL and TRUE only | PASS | ['NULL acreditado', 'devuelve carga provisional `(1,n,r)`', 'TRUE acreditado y reconocimiento completo', 'devuelve carga registrada `(1,n,r)`', 'FALSE/excepción o interrupción después de TRUE', 'jamás retry'] |
| arithmetic alignment B512 | PASS | max n multiple of B; interval fits; all eight requested quotas allowed |
| arithmetic alignment B1024 | PASS | max n multiple of B; interval fits; all eight requested quotas allowed |
| arithmetic alignment B2048 | PASS | max n multiple of B; interval fits; all eight requested quotas allowed |
| arithmetic alignment B4096 | PASS | max n multiple of B; interval fits; all eight requested quotas allowed |
| arithmetic alignment B8192 | PASS | max n multiple of B; interval fits; all eight requested quotas allowed |
| arithmetic alignment B16384 | PASS | max n multiple of B; interval fits; all eight requested quotas allowed |
| arithmetic alignment B32768 | PASS | max n multiple of B; interval fits; all eight requested quotas allowed |
| arithmetic alignment B65536 | PASS | max n multiple of B; interval fits; all eight requested quotas allowed |
| QA1-01 accounting counterexample resolved | PASS | 1179647 requested vs illustrative1179648 OS; total9437176 vs9437184 |
| ninth minimum arena inadmissible | PASS | count9/logical8913408/requested9438199 all exceed quotas |
| overflow pre-policy helper obligation | PASS | size_t maximum+padding overflows; small bound positive fits |
| full goal future K2 | PASS | ['K2 adquisición propia', 'FILE_OPEN/OPENED', 'CREATE/CREATED', 'registro pre-entry'] |
| full goal future K3 | PASS | ['K3 metadata/mode/streams/G2', 'parser streams limitado1MiB', 'no comparte `_RETAINED` U2'] |
| full goal future K4 | PASS | ['K4 ancla y S1 full-chain', 'root→proyecto→data→_storage', 'SECURITY_UNACCREDITED', 'no de un test hook `trusted=True`'] |
| full goal future K5 | PASS | ['K5 I/O exacto propio', 'no retries short/PENDING', 'No existe probe→ChainLease o probe→ACK'] |
| full goal future ST1 | PASS | ['ST1 store físico', 'Header y 64slots U1', 'ceros reales', 'seed/final existentes conflicto'] |
| full goal future ST2 | PASS | ['ST2 store CAS/ACK/replay', 'PREPARE+flush1+read', 'COMMIT+flush2+fullread/revalidate antes ACK', 'cero slot/efecto nuevo'] |
| full goal future ST3 | PASS | ['ST3 recovery causal', 'Clasificación C0–C7', 'rechazo solo no cumple recovery final'] |
| full goal future L1 | PASS | ['L1 bootstrap legacy', 'ReceiptLease/PublishedDiskBinding retenidos', 'no adoptar SMOKE/path/hash'] |
| full goal future L2 | PASS | ['L2 lifecycle/admisión', 'Intención ACK antes efecto y completion ACK antes éxito', 'retire writers JSON por ruta'] |
| full goal future E1 | PASS | ['E1 aceptación persistente', 'VHDX/ext4/UUID/namespace/restart/backup/E2E/manuales', 'Tampoco K1 aceptado acredita T05 o M1'] |
| preserved O2 S1 G2 and honest original experiment | PASS | ['ADR-0075/O2', 'ADR-0076/S1', 'ADR-0078/G2', 'ADR-0081/O2', 'exits originales1', 'global134→135', 'deltas1/0/0', 'No identifica el handle interno', 'No hubo APPEND_DATA'] |
| TDD and coverage future only | PASS | ['TDD n/a: prosa y arquitectura', 'RED causal antes', 'no sólo líneas del diff', 'se informa también ramas', 'No se agrega ahora harness'] |
| local link docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md -> docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md | PASS | exists at real canonical destination or fixed snapshot |
| local link docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md -> docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md | PASS | exists at real canonical destination or fixed snapshot |
| local link docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md -> docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | PASS | exists at real canonical destination or fixed snapshot |
| local link docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md -> ../../decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | PASS | exists at real canonical destination or fixed snapshot |
| local link docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md -> storage-journal-kernel-design.md | PASS | exists at real canonical destination or fixed snapshot |
| local link docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md -> spec.md | PASS | exists at real canonical destination or fixed snapshot |
| local link docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md -> improvement-plan.md | PASS | exists at real canonical destination or fixed snapshot |
| local link docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md -> ../../decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | PASS | exists at real canonical destination or fixed snapshot |
| local link docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md -> ../roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md | PASS | exists at real canonical destination or fixed snapshot |
| local link docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md -> ../roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md | PASS | exists at real canonical destination or fixed snapshot |
| official ledger-lint | PASS | exit0 with original UTF8 warning preserved |
| QA1 authentic NO-VERDE remains historical | PASS | 66PASS1FAIL exit1; not attributed to newSHA |
| source snapshot unchanged | PASS | {'scripts/storage_journal_windows.py': '8f0e7bdb4c5dda0b92d186ea8293861209efe9170e5c36d8ce21c7662395c973', 'packages/storage-guard/studio_storage_guard/receipt.py': '811a5782ab0b84c0252e552e871d976fd944ec8059591c9afc492370394846f5', '.cache/dev-cycle/m1/storage-journal-store-flush-probe-20261011/flush_probe_experimental.py': '087288e3c20f21877cdbbc624fa0e332d3a765134e1fef4b84c0f093308d3bf9', '.claude/dev.json': 'ee4728bbc6a88539c5f85c2050dcd1c1bea9ece58e93f5fafa4f2d497c2b70b1', 'docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md': '15b555c14bc54731223b914914e2a82a9b4d5138b945981f76aac2a5c85729a0', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md': '4b87e0f36d1e05b05a3274876006aabf7b5a8e7f1cee4208c80321d99c7acdab', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md': '489f7521786574c554e8a276cf1eeca68fad557b5aed6e9c9132d0338953eefa', 'AGENTS.md': '914438ce2743d757d6b0aca903cafb6abd7e5075676ae35ee6bb82b71a328789', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md': '7ab1bb1ec9b4c65b901ac2c1f73c493048482fdc0802098c35f5237b4dbf89b9', 'docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md': '71a54e543c589d41f255445b08daaaeeabb7a6b5745db2ae6b9e5175add581a8', 'docs/CONSTITUTION.md': 'b15df6b30747dbe594d97a8fe2f896509586da4b890de981c42c1f27234861b2', 'tests/test_storage_journal_windows.py': '145a8832b79aaa673b64b637a22ad42c37e4e437c2c636a4835cb8d302ba690f', 'docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md': '10fadd0c88b44b42778a739335204267664a3a94beb37620b34719d02fd034d6', 'docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-journal-store-flush-native-2026-10-11.md': 'beebed7aeff53b5fe1ffe4d347a1d2e96aa516f994f358c29ff572a554ec5a5c', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md': '47abeb0ccece79e7927e212f3a279df593c445675690a94577e2e73d83a80122', 'scripts/storage_journal.py': '5db83df2584f419177162054c02eda46c33abcca253bcf3b2130301bec6f6ea5', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md': '7ceae414e61d18f5821df1c55bef1e130ffdcd72612dfb5d09f222423cd6f839', 'docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md': 'b71f4940a6c297de922e5b63bf7a12567b2bdc139ee649ca7045e11cb2471eab'} |
| canonical guards unchanged during QA | PASS | {'AGENTS.md': '914438ce2743d757d6b0aca903cafb6abd7e5075676ae35ee6bb82b71a328789', '.claude/dev.json': 'ee4728bbc6a88539c5f85c2050dcd1c1bea9ece58e93f5fafa4f2d497c2b70b1', 'docs/CONSTITUTION.md': 'b15df6b30747dbe594d97a8fe2f896509586da4b890de981c42c1f27234861b2', 'docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md': 'b71f4940a6c297de922e5b63bf7a12567b2bdc139ee649ca7045e11cb2471eab', 'docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md': '15b555c14bc54731223b914914e2a82a9b4d5138b945981f76aac2a5c85729a0', 'docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md': '10fadd0c88b44b42778a739335204267664a3a94beb37620b34719d02fd034d6', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md': 'fba4df08da053b442c157de3696d33c88c1c430c43655607490114c9cd95efd9', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md': '489f7521786574c554e8a276cf1eeca68fad557b5aed6e9c9132d0338953eefa', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md': '4b87e0f36d1e05b05a3274876006aabf7b5a8e7f1cee4208c80321d99c7acdab', 'docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md': '47abeb0ccece79e7927e212f3a279df593c445675690a94577e2e73d83a80122', 'docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md': '71a54e543c589d41f255445b08daaaeeabb7a6b5745db2ae6b9e5175add581a8', 'scripts/storage_journal_windows.py': '8f0e7bdb4c5dda0b92d186ea8293861209efe9170e5c36d8ce21c7662395c973', 'scripts/storage_journal.py': '5db83df2584f419177162054c02eda46c33abcca253bcf3b2130301bec6f6ea5', 'tests/test_storage_journal_windows.py': '145a8832b79aaa673b64b637a22ad42c37e4e437c2c636a4835cb8d302ba690f', 'packages/storage-guard/studio_storage_guard/receipt.py': '811a5782ab0b84c0252e552e871d976fd944ec8059591c9afc492370394846f5', 'docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-journal-store-flush-native-2026-10-11.md': 'beebed7aeff53b5fe1ffe4d347a1d2e96aa516f994f358c29ff572a554ec5a5c', '.cache/dev-cycle/m1/storage-journal-store-flush-probe-20261011/flush_probe_experimental.py': '087288e3c20f21877cdbbc624fa0e332d3a765134e1fef4b84c0f093308d3bf9'} |
| tools unchanged | PASS | {'C:\\Users\\daycr\\.codex\\plugins\\cache\\daycry\\custom-agents\\1.21.1\\agent-kits\\qa\\qa-gate.py': 'f59a20c399d5c30e154e15d926f458690e7bfd2d225f1204c9fd0b9e92e77072', 'C:\\Users\\daycr\\.codex\\plugins\\cache\\daycry\\custom-agents\\1.21.1\\agent-kits\\qa\\coverage-check.py': '4227e86f5c49d3c8192ad2161a5986b386fb7f2e93ab31b95983884817a840c2', 'C:\\Users\\daycr\\.codex\\plugins\\cache\\daycry\\custom-agents\\1.21.1\\agent-kits\\shared\\ledger-lint.py': 'c56de53d4cf608ebaac5ad58f66f6e14f1d71950a5a1e94189831b725e71e0cd', 'C:\\Users\\daycr\\.codex\\plugins\\cache\\daycry\\custom-agents\\1.21.1\\agent-kits\\shared\\knowledge-find.py': '3b5506eac9d1588c18b896f217882472c127384291a1acae152ee99c17f3ebb4', 'C:\\Users\\daycr\\Development\\music-studio\\scripts\\env.ps1': '32b02ae27056706573c790e5a8f6091bf0a2df938fd9fe092e920c64859a5812', 'C:\\Users\\daycr\\Development\\music-studio\\.venv\\Scripts\\python.exe': 'd7ae287c3b0bcc389b245e6e777f0e4d1385197dd16b8c91488dc1ca563bb3f4', 'C:\\Users\\daycr\\Development\\music-studio\\.cache\\dev-cycle\\m1\\storage-journal-kernel-contract-qa2-20261011\\qa2_document_checks.py': '964d9cea7efb50c097da3a13a3cc03088e3d2615dcf3a2761c2e07ec15f402eb'} |

## Pendientes de implementación y aceptación

- [ ] ROOT verifica/adopta FIX1 y libera K1 a implementer fresco antes de RED.
- [ ] K1 TDD causal, native Windows memoria propia y ABI, Linux negativo, cobertura whole>=80% por archivo, revisión/QA independiente.
- [ ] K2–K5: adquisiciones, metadata/G2, autoridad deployer/RootContext/S1 full-chain y I/O exacto, sin fake grants ni promoción de probe.
- [ ] ST1–ST3: store físico, CAS/ACK/replay, bootstrap físico y recovery causal de cola bloqueada.
- [ ] L1/L2/E1: leases reales, bootstrap legacy, controller/lifecycle/admisión, provisión ext4/UUID, restart/backup, E2E y checklist manual M1 existentes.

Sin handoff documenter ni cierre T05/M1. ROOT conserva canon/ledger/markers; actual_usage=null. Evidencia congelada tras manifest, sin CAS ni escritura fuente.
