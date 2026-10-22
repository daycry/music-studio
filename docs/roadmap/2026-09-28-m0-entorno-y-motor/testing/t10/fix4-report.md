# T-10 — corrección del prompt instrumental

R10-09 corregido CPU: `request_for` usa exactamente `instrumental_style` del corpus y `[Instrumental]` para la letra en ambas superficies. Un caption ausente, vacío o de tipo incorrecto produce error explícito; no hereda el caption de canción con voz. Los demás casos conservan sus textos y controles. [Recibo](fix4-receipt.json).

RED: 24 casos fallaron antes de la corrección, incluidos los 18 instrumentales de tres perfiles, dos superficies y tres semillas. GREEN dirigido: 37 pasan. Suite ampliada: 127 pasan en 6,23 s. Cobertura oficial del único archivo de producción modificado: 54/55 = 98,18 %. Ruff y formato conformes. Root cotejó JUnit, JSON oficial, sellos y 59 fuentes; 55 ajenas intactas, cuatro preimages correctas. Las otras dos modificaciones de fixtures sólo añaden el caption instrumental requerido.

El agente original dejó pruebas y cambios, pero ya no figuraba en el inventario vivo. Un implementer fresco completó exclusivamente la entrega privada sin repetir pruebas ni editar fuentes. Sus registros no incluyen argv completos ni códigos de salida originales: aquí se acreditan resultados por JUnit y contenido, sin inventarlos. El inventario protegido cubre locks, corpus, cobertura raíz y planes anteriores, no una custodia histórica exhaustiva de todos los audios y recibos.

Revisión5 y QA4 independientes pendientes; no inferencia GPU ni aceptación musical en esta entrega. Planes y tomas anteriores no se reescriben. T-10 permanece abierta.
