# QA independiente CPU U2b1 — 2026-10-11

**NO-VERDE conjunto Windows/Linux.** Windows: 139 PASS, 0 FAIL, 0 SKIP. Linux real: 105 PASS, 5 FAIL, 29 SKIP. Se detiene la aceptación conjunta; ningún cambio de producto, test, config, ledger o Git. ROOT decidirá el FIX2 y el CAS posterior. T-05/M1 abiertos.

## Fuentes y entorno

Autorización efectiva: `release-root.md`, `release-root.receipt.json`, revisión2 A/B/C 0 gaps. Snapshot 24 fuentes readonly verificado antes/después, byte a byte. Runtime SHA `af192c76519d88e8b1cbd267a8326bf74e54a871dbcd5c0dc5a13a8297e56db4`; tests SHA `f36ada14128344840267aa87df13f5d7383d0bc1d3da8345be608c5b02d4ef7a`. Canon U2a no alterado. `sources-before.json`/`sources-after.json` registran canon, autoridades y notas ROOT autorizadas, sin atribuirles drift de producto.

Windows gestionado por `scripts/env.ps1`, `uv run --frozen --no-sync --all-packages`, Python 3.12.14 de `.venv`, sin instalaciones. Linux imagen existente `e0eaea0b1ce2ac5f3bb002c10dcb51070fbd8dcbae806228aaec727da923b302` (ID del contenedor propio retirado), imagen `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`; UID/GID10001, networknone, rootfsreadonly, capdropALL, NNP, fuentes RO. Fixtures nuevas exclusivas del namespace QA; las nativas con ACL protegida al CREATE. Sin modificación ACL de padres existentes. Inventario `lstat` regular y reparses stat-only, sin traversal de junction.

## Resultados completos

Los 139 nodos se ejecutaron completos por plataforma, sin -k ni deselection. [Windows JUnit](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa-20261011/raw/windows/junit.xml), [Linux JUnit](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa-20261011/raw/linux/export/results/junit.xml), [todos los nodos/fallos/skips](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa-20261011/raw/node-results.json). Los 29 skips Linux son específicos de Win32/fixtures nativas/last_error y están individualizados con su razón; no prueban el binding Windows.

Windows cubre ordinary/missing, metadata y SD, borrow vivo, owncloseonce, sharing write/delete en ambos órdenes, directorio rename/delete, hardlink/wrongtype y junction nueva rechazada sin traversal, más pruebas causales de los fixes A01/B01/B02/B03. Los witnesses permanecen en las carpetas `native-own-*`, `u2b1-native-own-*`, `fix1-child-*` y `child-reap-*.json`; las trazas subprocess contienen wait, stdout, stderr y exit. Los inventarios finales listan cada fichero concreto sin seguir alias.

### Fallos Linux conservados

- `test_observation_false_query_never_parses_plausible_buffer`: assert [] == [202]
- `test_observation_close_revokes_once`: candidate_windows_security.IOCompletionUnaccreditedError: Retirada del proceso propietario requerida
- `test_observation_context_preserves_baseexception_and_cleanup`: candidate_windows_security.IOCompletionUnaccreditedError: Retirada del proceso propietario requerida
- `test_observation_concurrent_query_close_serialized`: candidate_windows_security.IOCompletionUnaccreditedError: Retirada del proceso propietario requerida
- `test_observation_independent_contexts_serialize_native_calls`: assert False

Diagnóstico causal real en un segundo contenedor CPU propio sin fixtures/escritura: `raw/linux-diagnostic/stdout.txt`, `stderr.txt`, `receipt.json`. `ObservationDouble.GetFileInformationByHandleEx` llama `ctypes.set_last_error` (test línea820), ausente Linux. El runtime retiene arena/owner y encadena `IOCompletionUnaccreditedError` desde `AttributeError: module 'ctypes' has no attribute 'set_last_error'`; `fake.closed=[]` y `_RETAINED` verdadero. El primer test (línea978) esperaba `[202]` al cerrar un falso resultado y falla; cuatro pruebas posteriores reciben el poison retenido. `ctypes.get_last_error` también ausente Linux. Es una frontera del doble/test Win32 no portado, no evidencia de fallo nativo Windows; tampoco se convierte en PASS o SKIP. Requiere FIX2 separado test-only y QA nueva, ninguna corrección aquí.

## Cobertura oficial whole line+branch

| Plataforma | Líneas | Ramas | Total oficial | Excluidas |
|---|---:|---:|---:|---:|
| windows | 489/535 | 161/182 | 90.65550907% | 0 |
| linux | 431/535 | 129/182 | 78.10320781% | 0 |
| combined | 499/535 | 163/182 | 92.32914923% | 0 |

Un único módulo runtime íntegro: 535 statements y 182 branches; exclude_lines=[] y omit=[]. Se preservan DB SQLite `.coverage`, JSON, XML y reporte por plataforma. `Coverage.combine(strict=True,keep=True)` oficial sólo con aliases de rutas, sin editar líneas/ramas de datos. Gate cobertura Windows/combinada >=80: exit `0`. Gate funcional conjunto: exit1. Cobertura no borra los cinco fallos. Los subprocess causales no se instrumentan automáticamente por este runner; no se atribuye su ejecución a líneas cubiertas que no figuren en la DB padre. No se adopta 94,5607% actor como resultado QA.

## Recursos, procesos y conservación

Nueva medición nativa: cold131 → import150 (+19) → APIwarm150 → fixture151 → preflight159 (+8) → open160/close159 por12 → ownerclose158. Los +19/+8 quedan explícitos, sin restar ni alegar fuga global. SD raw padre e hijos12, metadata/identidad antes/después y import path/SHA en `native-resource-witness.json`, `native-resource-progress.json`, `resource-parent.rawsd`, `resource-child-*.rawsd`. Se comprobaron borrow y ownclose idempotente; la prueba sólo acredita estabilidad de operaciones/handles propios dentro de esa ventana. Históricos actor +19/+8 etiquetados separados, no son esta ejecución.

Windows `POSTPYTEST.json` autentica resultados/coverage/imports únicamente: stdout/stderr aún vivos quedan excluidos. `raw/windows/supervisor-reap.json` y `raw/native/supervisor-reap.json` contienen communicate/wait reales sobre wrapper, streams cerrados y SHA finales; runtime PID se registra separadamente y su auditoría posterior en `raw/windows-postwait-pids.json` no se presenta como wait directo.

Linux controller esperó al hijo real13 y cerró streams antes del tar físico; `process-reap.json`, `export-receipt.json`, `exec-export-receipt.json`, `tar-members.json`, `results.tar`, `commands.json` documentan export binario SHA/tamaño/miembros verificados antes de STOP. `container-final-inspect.json`: PID0, stopped; `cleanup.json`: rm correcto e inspect posterior ausente. Segundo contenedor diagnóstico `--rm` retirado, sólo su stdout/stderr sellados después communicate; no produce tar porque no escribe resultados en el contenedor. Sólo retirados contenedores propios. No errores de preparación del harness; fallos Linux completos preservados sin rerun de suite.

## Límites y pendientes

Sin I/O pending nativo: pending/unknown/inflight son dobles causales en hijos propios, con wait/reap real registrado por cada padre; retirar el proceso no acredita completion del I/O. No geometría, writer, bootstrap, ACK, store, fullchain, lifecycle, admin, WSL, GPU/Ollama, SMOKE/VHDX, servicios ajenos ni datos/BD. No UI/E2E ni manuales del plan ejecutados; ext4 persistente y M1 siguen abiertos.

ROOT verificará payload y decidirá FIX2 antes de adopción; no handoff documental ni cierre de estados. Tokens/eur/horas IA reales: null. [Recibo estructurado](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa-20261011/structured-receipt.json), [fuentes antes](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa-20261011/sources-before.json), [fuentes después](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa-20261011/sources-after.json), [gate oficial](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa-20261011/raw/combined/gate.json). `freeze.manifest.json` y `freeze.seal.json` sellan regulares SHA/tamaño y reparses stat-only; tras ese sello esta QA no vuelve a escribir.


## Verificación ROOT

ROOT verificó392payloads/1reparse stat-only/24fuentes, JUnit139porplataforma, imports del runtime/test por path/SHA, streams supervisor traswait,54recibosFIX1exit0/reaped(27porplataforma), TAR134miembros auténticos, contenedor retirado y diagnóstico Linux. Funcional conjunto1; noCASniaceptaciónM1. FIX2 limitada a fixture last_error requerida. Sin controlsham adicional en QA; actor futuro debe probarlo antes de editar. Contenedores backend anteriores4 retirados tras revalidar sus4TAR/miembros y guardarinspect/logs; ACE sigueUp. Informes archivados intactos.
