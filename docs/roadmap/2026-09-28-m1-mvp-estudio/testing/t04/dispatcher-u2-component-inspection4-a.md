**Lente A · T-04/U2 · inspección 4: 0 Critical / 0 Important / 0 Minor.** A3-01 corregido. Dictamen limitado al delta de dos archivos; no acepta U2 ni T-04 completa.

Los ✓ siguientes expresan conformidad del **delta revisado**, no cumplimiento íntegro del criterio.

| T-04 → criterio de aceptación | Resultado | Evidencia fichero:línea |
|---|---|---|
| GPU1/CPU2, prioridad/FIFO, `not_before`, CPU sin descargar GPU | ✓ A3-01 corregido: queued expulsa exclusivamente sus objetos y conserva el mapa del cursor retry | `admission.py:199`; `runtime.py:342`; `test_dispatcher_retry.py:1698`, `:1812` |
| Dispatcher mediante `EngineBackend` y adapter `/v1` | ✓ Sin modificación de protocolo o adapters | `runtime.py:17`; `tasks.md:184` |
| Cadena generación → post.audio → beats | ✓ Permanece explícitamente abierta y fuera de esta corrección | `tasks.md:185` |
| Resolver por tarea verificada | ✓ Sin modificación de su autoridad | `retry.py:19`; `tasks.md:186` |
| Unload y comprobación de VRAM libre | ✓ Conservado; la regresión nueva no ejecuta health/load/submit | `test_dispatcher_retry.py:1861`; `tasks.md:187` |
| NDJSON, reenganche por `seq` y bus SSE | ✓ Sin cambios en consumo o eventos | `runtime.py:21`; `tasks.md:188` |
| Retry durable, máximo dos y offload una vez | ✓ Se conserva la elegibilidad y reserva; ya no se invalida su cursor compartido | `retry.py:32`, `:122`, `:156`; `admission.py:201` |
| Recuperación con ID/payload durable; continuación CPU, manual y batch/serie | ✓ Sin cambios; las partes pendientes siguen abiertas | `tasks.md:190`; `tasks.md:816` |

| Comprobación transversal | Resultado y evidencia |
|---|---|
| **Alcance / Archivos** | ✓ Los dos cambios pertenecen a cola y tests previstos por `tasks.md:177` y Fase 2 de `improvement-plan.md:39`. Diff completo leído. Scope aislado: dos dentro, cero fuera, cero excluidos efectivamente; configuración sin exclusiones añadidas. |
| **Regresión A3-01** | ✓ Test leído línea a línea: misma Session, 801 filas por población, prioridades intercaladas, microsegundos y desempate por ID; secuencia exacta de 1602 `(id,status)`, páginas `400/400/1`, cierre anticipado y siguiente poll. `test_dispatcher_retry.py:1698`, `:1792`, `:1812`, `:1817`, `:1860`, `:1867`. |
| **Cobertura vigente** | ✓ Único módulo productivo modificado: **admission.py 195/206 = 94,660194 %**, cero exclusiones. Contrasté la traza SQLite original en modo lectura con el parser de las fuentes actuales: sentencias cubiertas y faltantes coinciden con `coverage-final.json`. Supera el 80 % sin medias, líneas del diff ni unión histórica. |
| **TDD causal** | ✓ RED original exit **1**, UTC **03:27:01–03:27:05**, anterior a producción **03:27:29**. JUnit y stdout contienen `InvalidRequestError` tras 1200 filas, ambos streams con `400/400`. La fuente archivada conserva `expunge_all()` y coincide con la preimagen. `red-native-causal.command.json:1`; `red-native-causal.stdout.txt:1`, `:217`. El CHECK inicial del fixture no se contabiliza como RED. |
| **Resultados preservados** | ✓ JUnit final: **428 PASS / 2 skips**, exit **0**. Comparación propia: los 428 casos anteriores conservan resultado; dos casos añadidos. Las 28 funciones/clases anteriores conservan AST exacto. Dos suplementos HTTP con MockTransport separados. `final-current.stdout.txt:84`. |
| **Constitución explícita** | ✓ Sin violaciones identificadas del server escritor, cola fijada, confinamiento o cierre con Verificación: `docs/CONSTITUTION.md:18`, `:20`, `:25`, `:33`. |
| **Verificación contractual y cierre** | ✓ T-04 sigue `en-progreso`, con ocho CA abiertos (`tasks.md:171`, `:183`). No hay cierre sin evidencia en este delta. La suite entregada no sustituye la Verificación completa de `tasks.md:180`; no la ejecuté para suplirla. |
| **Generados/descripciones E2/E3** | No aplica interop: el diff no toca `commands/`, `agents/` ni `hooks/`. No modifica contratos ni introduce una decisión documental nueva que requiera actualización. |
| **Custodia actual** | ✓ Comprobación propia SHA-256: **69/69** fuentes de entrega y **3/3** del freeze de revisión coinciden con las actuales; protegidos intactos. |

**Gaps: ninguno en el delta actual.** La corrección de [admission.py:201](/apps/server/app/queue/admission.py:201) resuelve el escenario de A3-01 sin sustituir el mapa compartido ni silenciar errores de detach.

Revisión ejecutada estrictamente en lectura: inspección de fuentes, hashes, AST, JUnit y cobertura original. Las ejecuciones nativas RED/GREEN son evidencia archivada de la entrega, no pruebas reejecutadas por esta lente. Backend sintético y HTTP MockTransport permanecen cualificados; QA independiente, U3 y aceptación completa siguen pendientes, sin reiniciar contadores ni reabrir hallazgos anteriores.