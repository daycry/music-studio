| Criterio | Gravedad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| Independencia GPU1/CPU2 | Important | `apps/server/app/queue/dispatcher.py:51` | Un backend CPU ejecutando `audio.beats` devuelve `busy`. El preflight de otro backend GPU libre retorna `False` antes de comprobar el dispositivo del modelo CPU. Bloquea una ejecución GPU compatible con los límites globales. |
| Resolver entre varios engines | Important | `apps/server/app/queue/resolver.py:266` | El primer backend configurado está caído y el job pide explícitamente otro backend disponible. `_catalog()` lanza `ResolutionError` antes del filtro `engine_id`; nunca se consulta el backend solicitado. |
| Selección con carriles ocupados | Important | `apps/server/app/queue/dispatcher.py:118` | Hay una ejecución GPU activa, otro job GPU prioritario encolado y un job CPU ejecutable detrás. `select()` devuelve siempre el GPU encolado; el preflight lo rechaza y `dispatch()` termina sin explorar el CPU. Las llamadas posteriores repiten el bloqueo mientras siga ocupado el carril GPU. |

Los dos primeros fallos se reprodujeron ejecutando las clases actuales en memoria con dependencias sintéticas inyectadas; el tercero se acredita por inspección estática. No son pruebas nativas de integración.

Los 11 archivos coinciden con el freeze. La cobertura oficial examinada supera el 80 % en cada módulo con sentencias y tiene cero exclusiones. No ejecuté suites ni modifiqué archivos.