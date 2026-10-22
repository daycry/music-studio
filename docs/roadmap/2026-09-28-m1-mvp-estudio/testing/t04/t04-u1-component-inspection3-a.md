**Lente A · inspección de componente U1 nº 3: 0 Critical / 0 Important / 0 Minor.** Sin defectos de requisitos o constitución identificados en el diff de cuatro archivos. **No acredita T-04 completa**: sigue `en-progreso`, con ocho CA abiertos y revisión formal integrada nº 4 pendiente.

Las rutas abreviadas corresponden a `apps/server/app/queue/` y `apps/server/tests/`.

| T-04 → criterio de aceptación | Resultado en esta entrega | Evidencia fichero:línea |
|---|---|---|
| CA1 · GPU1/CPU2, prioridad/FIFO, `not_before`, CPU sin descargar GPU | ✓ U1; cierre integrado pendiente | `admission.py:145,216,237`; `dispatcher.py:47,71`; `test_dispatcher_admission.py:282`; `test_dispatcher_scanning.py:118,395,436,453` |
| CA2 · Protocolo `EngineBackend` y transporte `/v1` | ✓ Transporte conservado; consumo completo pendiente | `backends/protocol.py:48`; `backends/http.py:136`; `test_queue_backend.py:29,122,276` |
| CA3 · Cadena generación → post → beats, N salidas y `seed+i` | ✗ Pendiente U3, declarado fuera de esta entrega | `tasks.md:185`; `test_dispatcher_admission.py:409` conserva explícitamente el límite de desbloqueo |
| CA4 · Resolver por tarea verificada y catálogo en caché | ✓ U1, incluida revalidación del seleccionado | `resolver.py:109,150,157,169,195`; `dispatcher.py:161,168`; `test_queue_resolver.py:146,192`; `test_dispatcher_scanning.py:315,329` |
| CA5 · Unload y comprobación de memoria libre | ✓ U1 para residencia propia acreditada | `dispatcher.py:71,107,126,142`; `test_dispatcher_admission.py:504`; `test_dispatcher_scanning.py:329,361` |
| CA6 · NDJSON, reenganche, progreso, telemetría y SSE | ✓ Transporte; ✗ integración U2 pendiente | `backends/http.py:231`; `test_queue_backend.py:219`; `tasks.md:188` |
| CA7 · Retryable, máximo dos retries y offload único | ✗ Pendiente U2 | `tasks.md:189`; `dispatcher.py:198` solo realiza la primera entrega |
| CA8 · Recuperación durable, retry manual y batch/serie | ✓ Reserva inicial y conservación ante incertidumbre; ✗ recuperación completa U2/U3/I-01 pendiente | `admission.py:216,318`; `test_queue_inputs.py:176`; `tasks.md:190` |

Los ✗ indican **trabajo pendiente declarado**, no gaps de esta unidad ni criterios cerrados indebidamente.

| Comprobación solicitada | Resultado y evidencia |
|---|---|
| Implementación de tareas hechas | ✓ Ninguna tarea se cierra en este diff. `tasks.md:171,183` mantiene T-04 y sus CA abiertos. |
| Alcance y `Archivos` | ✓ Los tres módulos de cola y `test_dispatcher_scanning.py` corresponden a `tasks.md:177` y `improvement-plan.md:39`. Sin cambios adicionales de esquema, contratos o infraestructura. |
| Tests por criterio | ✓ Leídos los tests completos y sus assertions: candidatura inválida, ventanas de 400/401/2001, dependencias, FIFO de microsegundos, snapshot finito, identidad/salud/VRAM frescas y ausencia de unload ante inputs inválidos. |
| Constitución explícita | ✓ Sin infracción identificada de `docs/CONSTITUTION.md:32,33,35,36,37,43,46,58,62,64,66`. |
| Verificación ejecutada al cerrar | N/A: T-04 permanece abierta. La suite focal no sustituye la verificación de `tasks.md:180`; no la ejecuté para suplir evidencia. |
| Generados E2 / interop | N/A: el diff no toca `commands/`, `agents/` ni `hooks/`. No corresponde ejecutar el exportador. |
| Descripciones E3 | ✓ La corrección conserva la decisión de staging y retención de `ADR-0049:10,12,14`, descrita en `docs/arquitectura/sistema.md:124` y `datos.md:116`. No introduce otro contrato o decisión contradictoria. |

**Los tres gaps de inspection2 están corregidos dentro de U1:**

| Gap anterior | Evidencia actual |
|---|---|
| B2-01 · `ResolutionError` abortaba el escaneo automático | `dispatcher.py:175` aísla el error por candidato; `test_dispatcher_scanning.py:73,105` comprueba continuación automática y ausencia de retarget explícito. |
| B2-02 · 400 cabezas inelegibles ocultaban el job ejecutable | `admission.py:145` recorre páginas acotadas; `test_dispatcher_scanning.py:118,418` comprueba múltiples ventanas, snapshot finito y revalidación actual. |
| D2-03 · Health/hash repetidos por job ocupado | `resolver.py:150,157` y `dispatcher.py:47,161` separan screening de resolución completa. `test_dispatcher_scanning.py:167` conserva hashes reales y conteos HTTP/ASGI. |

Cobertura oficial **completa por módulo cambiado**, comprobada directamente en `coverage-final.json`, sin promedio, combinación histórica ni exclusiones:

| Módulo | Cubiertas / sentencias | Cobertura | Excluidas |
|---|---:|---:|---:|
| `admission.py` | 183/196 | 93,37 % | 0 |
| `dispatcher.py` | 117/136 | 86,03 % | 0 |
| `resolver.py` | 151/163 | 92,64 % | 0 |

Contrasté argv, UTC, exit y JUnit originales: **189 PASS, cero fallos/errores/skips, exit 0**. Los RED válidos muestran fallos funcionales anteriores a las correcciones: excepción de cabeza, selección `None`, **402 hashes frente a 2**, unload indebido e identidad cambiada admitida. Los intentos inválidos de selector/fixture no se cuentan.

**Custodia comprobada por mí:** seis fuentes del freeze exactas; las 25 copias finales coinciden con su manifiesto; 73 rutas protegidas intactas. El helper externo `scripts/test_workspace.py` sí difiere actualmente, como declara la entrega: los 189 PASS acreditan sus bytes congelados, no el stack global actual. La QA integrada queda pendiente de alinear T08.

La evidencia nueva usa SQLite de fichero, WAV reales de 204 bytes y HTTP/ASGI con adapters sintéticos. No acredita engines GPU reales, Docker, Linux ni calidad musical. Mi revisión ejecutó únicamente comprobaciones de lectura y hashes; **no reejecutó suites ni modificó archivos**.