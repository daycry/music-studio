**1 Important · 0 Critical · 0 Minor.**

Alcance: `scope.diff` de inspección2, nueve ficheros; los doce hashes actuales coinciden con el freeze. Representa cambios sin commit, no un rango literal `<base>..HEAD`. Lente activada por rutas `queue` y `await` dentro de bucles.

| Criterio | Resultado | Fichero:línea y escenario de carga |
|---|---|---|
| N+1 de dependencias | ✓ | `admission.py:70`: consultas agrupadas. Evidencia nativa de entrega: **200/400/800 jobs → 2/2/3 SELECT**, con y sin dependencias. D-01 anterior corregido. |
| Hash bajo writer/event loop | ✓ | `resolver.py:213`, `dispatcher.py:131`, `admission.py:164`: hash y copia fuera del writer mediante hilos. Evidencia nativa de entrega: otro writer avanza y heartbeat **6/6** durante ambos hashes. D-02 anterior corregido. |
| Trabajo repetido al recorrer candidatos | **✗ Important D-03** | [dispatcher.py:124](../../../../../apps/server/app/queue/dispatcher.py:124): cada candidato se resuelve completamente **antes** de descartar su engine ocupado. Con **200 jobs GPU prioritarios dirigidos al mismo engine ocupado y un CPU detrás**, la sonda obtiene **401 consultas de salud al engine GPU y 201 resoluciones de entradas** antes de reservar el CPU. La caché conserva modelos, pero vuelve a consultar salud por candidato. Para **200 `audio.beats` pendientes sobre WAV FLOAT32 estéreo de 180 s/48 kHz**, el mismo recorrido también calcula SHA sobre **13,8 GB** de entradas antes de rechazarlos por ocupación. Este volumen es cálculo estático, no benchmark de disco. |
| Complejidad adicional | ✓ | Sin otro hallazgo independiente; el crecimiento evitable del recorrido queda recogido en D-03. |

D-03 aparece con el nuevo bucle de candidatos: antes se resolvía uno. Conviene reutilizar la observación de ocupación durante el recorrido y posponer el hash hasta identificar un candidato potencialmente despachable, conservando las revalidaciones antes del claim.

**Evidencia propia:** sonda en memoria con `Dispatcher` y `Resolver` actuales; candidatos, backends, entradas y reserva inyectados. Confirma los conteos, sin acreditar latencia HTTP ni hashing nativo.

**Entrega contrastada:** corrida final v2, argv/UTC/exit/JUnit: **150 PASS**; cobertura completa por módulo **85,56–100 %**, cero exclusiones. RED D-01/D-02 fallan por efectos funcionales. No reejecuté suites ni modifiqué ficheros. U2/U3 y aceptación íntegra T04 quedan fuera de esta revisión.