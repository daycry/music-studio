# T04 relación durable — revisión2

A/B/C/D estáticas frescas sobre nueve fuentes:0Critical,1Important,0Minor. R04-S01 corregido. Nuevo R04-B02: SQLite normaliza una fecha imposible como2026-02-30, mientras que Pydantic la rechaza; las guardas SQL admiten una fila que no se puede leer. Root confirma el comportamiento del parser SQLite y datetime estricto. Hace falta RED funcional y validación de calendario compatible, sin UDF ni modificar el wire.

A/B recibieron un ledger completo anterior a una nota global root; su bloque T04 suministrado permanece exacto y el archivo completo congelado se verifica. C/D recibieron el contexto actual. No se afirma que el ledger completo siguiera inmutable. Ninguna fuente de producto del paquete cambió durante revisión. Revisión3 llevará todos los veredictos originales, después QA. T04 permanece abierto.
