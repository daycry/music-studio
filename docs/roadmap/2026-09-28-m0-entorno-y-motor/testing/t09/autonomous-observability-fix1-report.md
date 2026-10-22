# T-09 — Fix1 de observabilidad autónoma, entrega CPU

Corrección propuesta para R09-O1–O5 en cuatro archivos, pendiente de revisión2 y QA. Root cotejó64fuentes/64preimágenes/60ajenasintactas,12documentos y los artefactos sellados. Runtime y .coverage raíz intactos.

La suite ejecutó138tests sin fallos; el suplemento final11, con5solapados y6nuevos:144únicos, no una suite de144. Coverage.py oficial597/745 (**80,1342%**) de tres archivos de producción completos modificados; Ruff, formato y gate exit0. Los seis tests adicionales quedan en el archivo canónico de tests. [Recibo](autonomous-observability-fix1-receipt.json).

Los RED conductuales originales preceden a cada corrección. Dos intentos con reloj de fixture incorrecto se descartaron. La metadata/log de dos suplementos intermedios fue sustituida en privado; no se cuentan ni se presentan reconstrucciones como originales. El primer gate79,3289% no se aceptó, y su extracción proviene del transcript. Comandos y resultados finales conservan originales verificables.

La corrección liga relojes de operaciones a la muestra, persiste contexto previo a adquisición, conserva baseline histórico durante resume, permite cadenas temporales de re-acreditación y usa cadencia por periodo. No cambia los umbrales. La interfaz de adquisición nueva está en el informe privado `.cache/dev-cycle/t09/autonomous-observability-fix1/report.md` y debe revisarse antes del collector real.

Ninguna GPU, piloto o matriz160 ejecutados. Los cinco gaps siguen pendientes hasta la revisión; T-09 permanece abierta. La aprobación documental T-20 anterior se preserva, con QA y cierre pendientes.
