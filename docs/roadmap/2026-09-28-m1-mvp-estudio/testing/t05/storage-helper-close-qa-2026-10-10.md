# QA independiente — T-05 Server.close — 2026-10-10

**VERDE del componente CPU/nativo; T-05 y M1 NO-VERDE.** Fuentes actuales tras CAS 21:32:34 UTC: Linux **91/91 PASS**, Windows focal **5/5 PASS**, cero fallos, errores u omisiones. Esta QA ejecutó de nuevo el producto; los resultados candidatos y las revisiones permanecen históricos. No se tocó producto, ledger, checkpoint, Git, GPU, WSL, ACE ni datos canónicos.

## Veredicto reproducible y fuentes

[Gate limitado](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/native-gate.json) se deriva de JUnit oficiales, exits reales y cobertura oficial; [script determinista](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/finalize.py). `qa-gate.py` no aplica al formato pytest nativo sin UI; no se fabrican JSON Playwright, capturas ni resultados E2E. Tampoco se cambia el marcador integral del plan.

```json
{
  "verdict": "VERDE-COMPONENTE",
  "scope": "Server.close CPU/nativo, no T05/M1 integral",
  "linux_junit": {
    "name": "pytest",
    "errors": "0",
    "failures": "0",
    "skipped": "0",
    "tests": "91",
    "time": "4.434",
    "timestamp": "2026-10-10T21:35:54.717285+00:00",
    "hostname": "f65580458dbf"
  },
  "windows_junit": {
    "name": "pytest",
    "errors": "0",
    "failures": "0",
    "skipped": "0",
    "tests": "5",
    "time": "0.170",
    "timestamp": "2026-10-10T23:35:14.996801+02:00",
    "hostname": "local-ai"
  },
  "whole_helper": {
    "covered_lines": 145,
    "num_statements": 151,
    "percent_covered": 93.90862944162437,
    "percent_covered_display": "94",
    "missing_lines": 6,
    "excluded_lines": 0,
    "percent_statements_covered": 96.02649006622516,
    "percent_statements_covered_display": "96",
    "num_branches": 46,
    "num_partial_branches": 6,
    "covered_branches": 40,
    "missing_branches": 6,
    "percent_branches_covered": 86.95652173913044,
    "percent_branches_covered_display": "87"
  },
  "minimum": 80,
  "source_17_unchanged": true,
  "linux_pytest_exit": 0,
  "qa_gate_py": "NO APLICA: pytest nativo sin UI; no JSON Playwright sintético",
  "T05_M1": "NO-VERDE",
  "utc": "2026-10-10T21:37:09.268331+00:00"
}
```

17 fuentes actuales comprobadas por bytes/SHA antes y después, iguales al snapshot; [antes](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/source-before.json), [después](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/source-after.json). Helper SHA `d2c331026b2c8e8b3665b8d520039f1023e29545e16894b1f36b8f895b27dc8c`; test SHA `bd4af77ab8f3c9eb3bb0d7ae6ef9f3802f6962c10355dc4d84463acc0370190b`.

## Ejecución actual y cobertura

Linux: protocol/helper/client originales **90 casos**, más un probe QA independiente real **1 caso**. [JUnit Linux](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/current2/results/junit.xml), [stdout completo](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/current2/start.log), [terminal start](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/current2/start.terminal.json), [terminal Docker mínimo](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/current2/docker-terminal.json). Contenedor propio `qa-m1-helper-close-current2-20261010`, PID final 0, exit 0, imagen fijada `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`. Permanece detenido para revisión forense. [comando/runner](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/run.py), [launcher actual](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/current2/launcher.py).

WHOLE helper: **145/151 statements = 96,02649 %**, ramas **40/46 = 86,95652 %**, combinado **185/197 = 93,90863 %**, umbral 80 %, **0 líneas excluidas**. No es sólo diff ni función close. [coverage oficial](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/current2/results/coverage.json); seis statements y seis ramas quedan sin cubrir. Instrumentación `coverage.py` anterior a pytest/imports, con metros reales de hijos `fork` y combinación; datos conservados.

Windows: cinco variantes de liberación de todos los handles/causa primaria, **5 PASS**, 23 no seleccionados; [JUnit](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/windows-junit.xml), [stdout](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/windows-focus.log), [terminal](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/windows-focus.terminal.json). Ruff y format afectados: exit 0, dos archivos ya formateados; [Ruff](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/ruff.log), [format](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/ruff-format.log). Aviso común no funcional `cache_dir` desconocido por desactivar cacheprovider conservado.

## Contratos nativos medidos

La suite prueba autenticación real AF_UNIX/SOCK_SEQPACKET/SCM_RIGHTS con helper UID19000 y consumidor UID10001, exclusión de segunda instancia, rechazo de peer incorrecto, conservación de socket extranjero, cierre idempotente y limpieza de dominio. `_credentials` comprueba en los hijos **CapEff/CapPrm/CapInh/CapAmb=0 y NoNewPrivs=1** mediante `/proc/self/status`. CapBnd conserva exclusivamente cinco capacidades de setup del contenedor; no se afirma que todos los Cap* sean cero. Parent fixture UID0 con SETUID/SETGID/CHOWN/DAC_OVERRIDE/FOWNER, drop ALL, no SYS_ADMIN, sin privileged y red none; no describe las credenciales del runtime principal.

El [probe QA](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/current2/inputs/test_qa_close.py) cierra un FD real, abre otro archivo y acredita reutilización del mismo número antes de lanzar EINTR. Close intenta ambos FDs una vez, traduce la causa, el segundo cierre no repite llamadas y el FD extranjero permanece escribible; conteo real inicial/final igual. No es un mock de FD. El test usa un socket Unix real y rutas temporales propias.

`/scratch` tmpfs sólo para fixtures unitarias; UUID/ioctl e inspección ext4 son seams declaradas de estos tests. **No acredita almacenamiento ext4 del producto, VHDX, mount, attach, CAS durable, controller, persistencia, recovery integral ni publicación real.** `/out` vive en capa Linux persistente del contenedor propio y se exportó tras su terminación a evidencias; no es tmpfs ni datos de producción. Principios locales y aislamiento de datos de la Constitución respetados.

## Intento fallido preservado

Primer contenedor `qa-m1-helper-close-current-20261010`: arnés creó `/out` 0755 en vez de 01777; los hijos no podían guardar cobertura/JUnit, hubo PermissionError y espera en pipes. Sólo ese contenedor fue detenido, exit **137**, PID final 0. [stdout íntegro](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/start.log), [log diagnóstico](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/failed-harness-full.log), [estado terminal](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/docker-terminal.json). Evidencias parciales intactas en `results/`; no se cuentan como producto aprobado ni como fallos atribuibles al producto. Corrección exclusivamente launcher QA a 01777, equivalencia con fixture original. Segunda ejecución pasó sin fallos; no se oculta la primera. Inspecciones exportan configuración mínima sin Env.

## Puertas integrales y pendientes

[ledger-lint](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/ledger-lint.log): **0 incoherencias**, aviso existente de UTF-8 leído con reemplazos. [coverage-check](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/coverage-check.log): **0 referencias rotas**, T-00 sin cobertura declarada; aviso integral conservado, no decidido aquí. [exits](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/entry-gates.json). Esta QA no ejecuta ni acepta E2E/API/A11Y de M1.

- [ ] Persistencia y publicación real ext4/VHDX, controller/validated/detach/recibo durable.
- [ ] Recovery/assets/Range/backup y gate integral T-05/M1.
- [ ] Manuales M-01 escucha humana, M-02 y M-03 del plan.

PDF omitido: dependencias gestionadas ausentes y omisión autorizada; se leyó `custom-agents:to-pdf`, no se instaló nada. [estado PDF](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/pdf-status.json). Sin cierre de estados, handoff a documenter ni publicación Confluence/Jira.

[Inventario propio](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/artifact-inventory.json), [sello SOURCE_SEAL_FINISHED](../../../../../.cache/dev-cycle/m1/storage-helper-close-20261010/qa/source-seal.json). Tokens/coste reales desconocidos; sólo marcador del lote ROOT, sin marcador solapado de este agente.
