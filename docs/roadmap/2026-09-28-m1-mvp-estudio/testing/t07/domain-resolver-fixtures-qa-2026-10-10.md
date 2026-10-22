# QA independiente — T-07, fixtures del resolver

**Verde en esta subunidad técnica:** Windows 18/18 y Linux Docker 18/18; 0 fallos, 0 errores, 0 omisiones en las ejecuciones finales. No cierra T-07 ni M1.

Fuente actual tras CAS del orquestador (21:44:41 UTC): `apps/server/tests/test_domain_routes.py`, SHA-256 `3c9c12920b915e9c23fc966764be2207d10c6b6bec4fe3f64f47bfdacd54e5e7`. Las únicas diferencias AST respecto de la preimagen son dos keywords `engine_id="mock"` en returns de fixtures; todas las aserciones anteriores y el runtime se conservan.

| Entorno | Evidencia oficial | Salida real | Imports privados |
|---|---|---|---|
| Windows, Python gestionado | [JUnit](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/windows/junit.xml) / [stdout](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/windows-run.log) | 0; 18 pasadas | 58 |
| Linux CPU, imagen congelada | [JUnit](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/linux2/junit.xml) / [stdout](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/linux2-start.log) | 0; 18 pasadas | 58 |

[Recibo Windows](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/windows/pytest.receipt.json) y [recibo Linux](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/linux2/pytest.receipt.json) acreditan rutas de módulos dentro del snapshot actual. [Ruff check](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/ruff-check.log) y [Ruff format --check](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/ruff-format.log): exit 0. Se ejecutaron de nuevo los 18 casos originales, incluida entrada de generación, estilo/seed, autorizaciones y cadena persistida; no se reutilizó el GREEN del candidato anterior ni se modificaron aserciones.

Linux usa la imagen `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`, UID/GID 10001, `cap-drop ALL`, `no-new-privileges`, red `none` y fuentes en bind de solo lectura. [Estado terminal](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/linux2-docker-terminal.json): contenedor propio `qa-m1-domain-resolver-current-20261010-linux2`, PID 0, detenido, exit 0, conservado para revisión forense. [Runner](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/retry_linux.py). Resultados, JUnit y logs persistidos en bind; únicamente los temporales de captura de pytest viven en `/tmp` Linux.

Primer intento: [log preservado](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/docker-start.log) / [estado terminal](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/docker-terminal.json), exit 1 antes de ejecutar casos: `FileNotFoundError` al truncar el archivo temporal de captura en bind Windows. El segundo contenedor cambia solo la ubicación temporal a Linux; conserva fuentes, imagen y casos. Se declara este fallo de infraestructura; no se presenta como un test flaky aprobado ni se oculta.

[182 fuentes antes](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/source-before.json) y [182 fuentes después](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/source-after.json) idénticas, con bytes/SHA por archivo. [Validación determinista](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/validation.json). El snapshot contiene `conftest.py` y el helper ACE de input; imports privados comprobados, sin mezcla con fuentes del checkout compartido.

`qa-gate.py`: **n/a**, subunidad sin UI y resultados oficiales pytest/JUnit. No se fabricó `results.json` de Playwright. No se atribuye cobertura E2E, ejecución de UI ni cobertura integral de backend. Cobertura sobre runtime cambiado: **n/a**, cambio exclusivamente en fixtures; no se calcula ni se afirma un 80 % nuevo. La cobertura histórica 655/755 (86,75 %) pertenece a otra ejecución del orquestador, no a este informe.

PDF omitido conforme al alcance autorizado: dependencias gestionadas ausentes; no se instalaron paquetes ni navegadores. Sin GPU, torch, WSL, privilegios administrativos, servicios externos ni acceso a datos canónicos. No se alteraron ledger, checkpoint, fuentes compartidas ni Git. Tokens/coste: null en el lote del orquestador, sin duplicar métricas.

## Comprobaciones manuales pendientes

- [ ] UI/E2E y manuales del plan M1: fuera de esta subunidad, pendientes de su auditoría global.
- [ ] Generación real ACE/GPU, almacenamiento durable ext4 y escucha humana: sin evidencia nueva en esta QA CPU.

Inventario íntegro con bytes y SHA: [artifact-inventory.json](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/artifact-inventory.json). Sello de finalización: [SOURCE_SEAL_FINISHED](../../../../../.cache/dev-cycle/m1/domain-resolver-fixtures-20261010/qa/SOURCE_SEAL_FINISHED.json). Los dos archivos autorreferentes se excluyen explícitamente de su propio inventario; el informe se sella dentro de él.
