# Revisión de dos lentes — intento 2: observabilidad autónoma T-09

Lentes **A+B+D**, tres contextos frescos terminales; Cfalse/Dtrue por selector oficial, scope0 sin avisos/info/exclusiones de usuario. Root64fuentes y12documentos sin deriva. Delta completo de cuatro archivos leído por archivo. Resultado: **0 Critical / 1 Important / 0 Minor**.

| ID | Veredicto | Evidencia o residuo |
|---|---|---|
| R09-O1 | corregido CPU | Relojes de operaciones y FILETIMEs ligados a la adquisición; control y variantes inválidas comprobados. |
| R09-O2 | corregido CPU | Originales/contexto previo completos; prueba de préstamo de sesión rechazada. |
| R09-O3 | corregido CPU | Baseline histórico preservado y nuevo baseline sólo tras health idle/loadednull. |
| R09-O4 | corregido CPU con residuo R09-O4a | Cadena preserva y valida segmentos; nuevo defecto de reloj histórico cuando WSL/browser siguen a Windows. |
| R09-O5 | corregido CPU | Muestra1,6s no suma espera fija; operación5s termina con gapmáx1,602996s. |
| R09-O4a (B2-01) | pendiente | benchmark_observation.py:585 usa finWindows+1ms para now histórico. Windows90,01/WSL90,21: muestra válida con now90,3, cadena rechazada auto_query_bracket_invalid con now90,011. |

El residuo R09-O4a requiere corrección. A consideró la cadena conforme en los casos nominales; la reproducción más específica de B con consultas secuenciales prevalece. Observers consulta NVML→Windows→WSL→browser, por lo que el fin de Windows no representa el fin de toda la adquisición. No se relajan umbrales ni se re-certifica historia.

A comprobó84sellos, JUnit138+11/144únicos, cobertura oficial597/745=80,1342% de tres archivos, delta/preimágenes y una sonda de frescura (control y tres rechazos), sin repetir suite. B ejecutó18tests dirigidos y reprodujo muestra secuencial válida/cadena rechazada. D ejecutó2dirigidos y una operaciónCPU propia5s con muestras1,6s:5muestras/gapmáximo1,602996s/done; la validación de una cadena de24.000muestras sintéticas y64fuentes costó3,399s. No demostró degradación material; no se añade un gap especulativo. Son pruebas CPU, no GPU ni RTF.

El primer ensayo temporal de D falló por FILETIME sintético en borde del bracket; el control válido situó el FILETIME dentro del intervalo. Esa corrección de fixture no modifica código de producto. No sumar los tests solapados a144 ni presentar una suite única inexistente.

T-20 documental permanece conforme y sus12fuentes intactas; QA/cierre pendientes. Historia anterior de T-09 y aprobaciones de revisión1 se conservan, sin rebates ni deuda. Siguiente: fix2 con RED propio del reloj histórico → revisión3 de3 sobre ese delta → QA independiente → piloto real y matriz160. T-09 permanece abierta.
