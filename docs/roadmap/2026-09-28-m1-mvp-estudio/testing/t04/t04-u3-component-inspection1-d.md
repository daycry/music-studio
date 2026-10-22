**1 Important; 0 Critical; 0 Minor.** Revisión del diff U3 congelado de ocho archivos; sus hashes coinciden con las fuentes actuales.

| Criterio | Resultado | Fichero:línea y evidencia |
|---|---|---|
| N+1 dentro de una ventana | ✗ Important D-01 | `admission.py:235` → `references.py:115`, `:137`, `:142`. La validación individual añade consultas bajo el writer. |
| Bloqueos síncronos en async | ✓ | `dispatcher.py:186`, `chains.py:172`, `manual_retry.py:34`: SQLite y comprobaciones de archivos se delegan a hilos. |
| Trabajo repetido evitable | ✗ D-01 | `references.py:54`, `:72`: cada salida de un mismo padre vuelve a consultar la misma arista y el mismo intento. |
| Complejidad y staging | Sin otro hallazgo | Variantes limitadas a 64 y ventanas a 400. SHA y copia permanecen fuera del writer; su coste previo no constituye una regresión nueva demostrada. |

**D-01 — Important: consultas por referencia bajo el writer de SQLite.**

En una ventana de **400 jobs `audio.beats` bloqueados**, cuyos padres `post.audio` ya terminaron y cuyos masters están disponibles, `candidate_batches()` valida cada job individualmente mientras conserva el writer (`admission.py:226`). Cada validación ejecuta tres SELECT explícitos: asset, existencia de dependencia y padre post. Son **1.200 SELECT adicionales**, más las búsquedas por identidad, frente a unas pocas consultas por lotes para esas relaciones.

También un `post.audio` de **64 salidas** consulta **64 veces la misma arista y 64 veces el mismo intento ganador**: 128 SELECT donde bastarían dos para esas entidades compartidas. Esto alarga la exclusión de otras escrituras durante el desbloqueo. La ventana acota memoria, pero conserva este N+1.

Corrección sugerida: precargar las relaciones de la ventana y reutilizar arista/intento por identidad, manteniendo las comprobaciones actuales de pertenencia, estado e índice.

**Evidencia:** análisis estático del flujo y conteo de consultas explícitas; no ejecuté benchmarks ni repetí suites. Contrasté los logs originales del último baseline —471 PASS, 2 SKIP, exit 0—, los RED funcionales y la cobertura completa actual de los cinco módulos: 83,56–98,80 %, cero exclusiones. Esa evidencia no acredita latencia bajo carga.

La lente se activó por rutas `queue` y patrones `await-en-bucle`, según `.cache/dev-cycle/m1/t04-u3-component-inspection1/lens-selection.json`.