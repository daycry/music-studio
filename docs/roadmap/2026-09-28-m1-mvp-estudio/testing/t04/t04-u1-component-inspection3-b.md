**0 Critical · 1 Important · 0 Minor.**

| Criterio | Resultado | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| Aislar errores de candidatura durante la reserva | **Important B3-01** | [dispatcher.py:190](../../../../../apps/server/app/queue/dispatcher.py:190) | El input pasa `resolve()`, pero cambia antes del staging o su referencia se elimina antes de la revalidación transaccional. `reserve()` lanza `ResolutionError` fuera de los bloques de captura. `dispatch()` aborta sin visitar el job válido siguiente, aunque haya capacidad disponible. |

**Prueba propia ejecutada:** dispatcher actual con dependencias sintéticas en memoria e inyección de `ResolutionError("Input changed during staging")` en la reserva. La excepción escapó y sólo se visitó la cabeza. No constituye prueba nativa SQLite; los caminos reales que producen esa excepción se comprobaron estáticamente en admisión y staging.

Los seis hashes coinciden con el freeze. Evidencia oficial comprobada: **189 PASS**, cobertura completa de los tres módulos cambiados **93,37 % / 86,03 % / 92,64 %**, cero exclusiones. Sin escrituras ni reejecución de suites.