**0 Critical · 2 Important · 0 Minor**, dentro del alcance U1.

| Criterio | Gravedad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| Continuar tras una candidatura no resoluble | Important | `apps/server/app/queue/dispatcher.py:124` | El primer job solicita un engine caído o una capacidad que ya no está verificada. `resolve()` lanza `ResolutionError` fuera del `try`, abortando el despacho antes de explorar un job CPU válido posterior. Como la cabeza sigue encolada, las llamadas siguientes repiten el bloqueo. |
| Alcanzar jobs elegibles fuera de la primera ventana | Important | `apps/server/app/queue/admission.py:139` | Hay 400 jobs `interactive` del mismo carril con `not_before` futuro y un job `normal` ejecutable detrás. El `LIMIT 400` se aplica antes de comprobar elegibilidad: devuelve únicamente los futuros y después los descarta. Cada despacho repite la misma ventana, dejando el carril libre y el job ejecutable sin atender. También ocurre con 400 dependencias pendientes. |

El primer defecto se reprodujo ejecutando la clase actual en memoria con dependencias sintéticas: sólo se visitó la candidatura fallida. El segundo se acredita por inspección estática del selector, la vista y los filtros; no ejecuté una prueba nativa de integración.

Las 12 fuentes coinciden con el freeze. Cobertura oficial v2 comprobada: cada módulo con sentencias supera el 80 %, con cero exclusiones. Sin escrituras ni ejecución de suites.