# T04 relación durable — revisión3

A/B/C/D frescas estáticas sobre diez fuentes/scope0. R04-S01 y R04-B02 corregidos. Resultado después de adjudicación:0Critical,0Important,0Minor pendientes.

B señaló que un timestamp UTC con espacio fallaría en snapshots.validate. Root ejecutó el caso exacto en SQLite privado: INSERT, project y validate pasan y conservan el texto. El entorno fijado no registra un checker date-time; FormatChecker omite formatos sin checker. **R04-B03 descartado (rebatido)** con evidencia nativa y código de la biblioteca instalada. No se certifica una validación RFC3339 estricta opcional ni comportamiento de clientes externos; QA comprobará paridad y roundtrip de este caso en wheel/Docker.

71 casos nuevos, suite vecina305pass/1skip, helper184/19693,88%0exclusiones.10fuentes finales custodiadas; import de fixture corregido tras suite vecina con helper idéntico y71 casos finales repetidos. QA independiente siguiente; T04 mantiene ocho criterios abiertos.
