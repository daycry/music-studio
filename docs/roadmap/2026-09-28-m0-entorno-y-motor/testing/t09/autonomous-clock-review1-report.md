# Revisión de dos lentes — observabilidad, intento5 (clock1)

Lentes A+B+D frescas: **0 Critical / 1 Important / 0 Minor**. A conforme con alcance, constitución, TDD y documentación. B detecta B-clock-01: StandardBias se usa cuando StandardDate no tiene mes; Windows ignora ese campo. Reproducción CPU legítima sinDST rechazada con auto_filetime_conversion_invalid. D no detecta regresión material; validación histórica lineal fuera del tick y reinicio de previous_sample conservado.

| Hallazgo | Grado | Evidencia | Decisión |
|---|---|---|---|
| B-clock-01: ajuste horario ignorado aplicado | Important | benchmark_clock.py:119; JUnit independiente1failed; control45passed | Corregir con RED propio antes de QA/GPU |
| Requisitos/precisión/conversión/históricos | Conforme CPU | A34 dirigidos, B45 dirigidos; solapados, no sumarlos | Mantener aprobaciones salvo este caso nuevo |
| Coste de validación | Conforme | D28 dirigidos y sonda24.059samples3,974s fuera del tick | No microoptimización ni cambio de cadencia |

Sesenta y seis fuentes y doce documentos intactos. Contextos nuevos despachados secuencialmente por límite real de threads; ningún revisor reutilizado. La historia previa no se resetea: este seguimiento5 corresponde al nuevo fallo realR09-O6; clock1 es sólo la identificación del delta. Root continúa la corrección acotada bajo delegación explícita del propietario. Sin deuda, umbrales relajados, acreditación GPU o cierre M0.

Semántica oficial: [TIME_ZONE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/timezoneapi/ns-timezoneapi-time_zone_information) indica que StandardBias y DaylightBias se ignoran cuando no están sus respectivas fechas. La revisión reproduce el caso sin cambiar la configuración del equipo.
