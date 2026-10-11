# T-05/U2b1: QA2 independiente y aceptación del componente

ROOT verificó la evidencia y adoptó el componente a 2026-10-11T10:35:13.197152+00:00. **PASS de unidad CPU Windows/Linux**, sin aceptación de T-05/M1 completos.

| Plataforma | Pasadas | Fallos/errores | Omitidas | Cobertura whole oficial |
|---|---:|---:|---:|---:|
| Windows |139|0|0|90,655509%|
| Linux Docker CPU |110|0|29|77,684798%|
| Unión oficial de cobertura |—|—|—|90,655509%|

Se ejecutaron los139 nodos completos por plataforma; identidades y29 omisiones Linux, con sus motivos, coinciden con QA1. Las omisiones de API/fixtures Windows no acreditan comportamiento nativo Linux. Gate funcional conjunto0 y gate autorizado Windows/combinada≥80%0. No se exige artificialmente que Linux cubra las ramas nativas Windows; se publica su porcentaje separado, inferior80.

Coverage oficial mide535 statements/182 branches del módulo completo, sin exclude_lines, omit, pragmas ni recorte del diff. Windows489líneas/161ramas, Linux427/130, combinación489/161. ROOT lee las DB y verifica unión exacta946arcsWindows∪780arcsLinux=946: Linux no añade arcs exclusivos en esta ejecución. Los hijos causales no se instrumentan automáticamente y su ejecución no se atribuye a líneas ausentes de la DB.

## Corrección y revisión

La primera QA conservada tuvo cinco fallos Linux: el doble llamaba ctypes.set_last_error ausente y producía poison antes de devolver FALSE. FIX2 añade get/set_last_error únicamente dentro de false_queryLinux mediante monkeypatch restaurable. Los asserts siguen exigiendo error5, cierre202 y ausencia de retención. F1fallo y F3control ejecutan la misma preimagen f36ada; el diagnóstico F2 propio ocurrió después deF3, con diagnósticoQA1 previo disponible. El primer harness reconstruido se identifica como posterior, sin inventar sello contemporáneo.

[Revisión1](storage-nt-observation-u2b1-review1-2026-10-11.md), [revisión2](storage-nt-observation-u2b1-review2-2026-10-11.md) y [revisión3](storage-nt-observation-u2b1-review3-2026-10-11.md) conservan tablas completas. Cuatro Important de revisión1 corregidos en2; revisión3A/B sin gaps sobre FIX2, C/Dauto false. El [informe QA1](storage-nt-observation-u2b1-current-qa-2026-10-11.md) permanece sin borrar ni convertir sus fallos en éxitos.

## Fuentes y comprobaciones ROOT

Runtime adoptado `af192c76519d88e8b1cbd267a8326bf74e54a871dbcd5c0dc5a13a8297e56db4`. QA2 ejecutó tests `020aeffe612e1c43aa1c420c4f969babfabf277f269ca96050d6d6c7d9c5adfe` y26fuentes readonly con imports/path/SHA verificados. Después de aceptar, Ruff exigió dividir una llamada en varias líneas: el formateo automático deja tests `3de1e82cd6292ed1ae6bb6ed737900ff0e877b24e46959535fb6632703f217ce`, con AST idéntico y runtime intacto. Se preserva la preimagen y no se atribuye el SHA posterior a la ejecución anterior. Ruff check0 y format--check0 finales; el primer format--check1 es un fallo de formato conservado, no de comportamiento. No se repitió una suite verde por ese cambio mecánico.

ROOT verificó361payloads regulares y1reparse mediante stat sin traversal; snapshot26 sin cambio, resultados/JUnit/imports/POSTPYTEST, streams finales después communicate/wait,27hijosFIX1 por plataforma exit0/reaped y sus hashes. Windows wrapper/runtimePID separados; auditoría posterior no equivale a wait directo del runtime. Linux TAR físico675840bytes/134miembros, SHA8a5d59273b62965bbeeed4ed4bd80dac0534eb05ddb9f0fa86c3f48899f7c44e autenticado antesSTOP; contenedor propio detenidoPID0, retirado y ausente. ImagenCPU7c65existente, UID/GID10001, rednone, rootfsRO ycapdropALL; sin GPU/build/pull/WSL/admin ni servicios ajenos.

No se repitió el probe extra de recursos: QA1, sobre el mismo runtimeaf192, conserva cold131→import150(+19)→APIwarm150→fixture151→preflight159(+8)→open160/close159×12→ownerclose158. Es evidencia histórica independiente, no medición QA2 ni ausencia global de fugas.

## Evidencia y límites

[Informe QA original](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa2-20261011/report.md), [recibo](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa2-20261011/structured-receipt.json), [JUnitWindows](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa2-20261011/raw/windows/junit.xml), [JUnitLinux](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa2-20261011/raw/linux/export/results/junit.xml), [gate](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa2-20261011/raw/combined/gate.json), [freeze](../../../../../.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa2-20261011/freeze.manifest.json). Evidencia ROOT en `.cache/dev-cycle/m1/storage-nt-observation-u2b1-qa2-root-20261011/`: verification-root, adoption-root y format-equivalence receipts.

El alcance aceptado es apertura relativa de objetos existentes, metadata readonly y custodia/cleanup. Pending/unknown son dobles causales, no I/O pending nativo ni garantía ante interrupciones repetidas del handler. No acredita geometríaU2b2, bootstrap/fullchain, store/readview/writer/ACK, journal durable, lifecycle, montaje ext4, E2E persistente, UI o manuales. T05/M1 abiertos. Tokens/eur/horasIA realesnull.
