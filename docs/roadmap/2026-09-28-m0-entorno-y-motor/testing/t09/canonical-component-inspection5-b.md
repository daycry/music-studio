**2 defectos Important; 0 Critical y 0 Minor.**

| Criterio | Gap | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| Transporte de progresos válidos | B5-01 · Important | `scripts/eval/benchmark_canonical_runtime.py:219` y `:204` | El waiter admite solo dos mensajes y `deliver()` usa `put_nowait`. Si el lector recibe tres progresos antes de que el caller vuelva a ejecutarse, el tercero provoca `queue.Full`: se revoca una operación válida aunque el protocolo permita 64 progresos. |
| Preservación del error original | B5-02 · Important | `scripts/eval/benchmark_canonical_runtime.py:301` y `scripts/eval/benchmark_process.py:85` | Tras recibir algún progreso del mux, un timeout o fallo construye `WorkerFailure/WorkerDeadline` con mensajes que contienen `payload`. El constructor busca `["value"]` y lanza `KeyError('value')`, perdiendo el error original y su evidencia de cleanup. |

Ambos reproducidos mediante sondas propias en memoria con definiciones AST de las fuentes actuales; sin hijos nativos, escrituras ni suites.

Freeze de los cuatro archivos coincidente. Evidencia oficial revisada: 64 PASS/1 PDH deselected; cobertura whole proceso **81,5832 %** y runtime **84,6330 %**, cero exclusiones. Estas ejecuciones son evidencia de entrega, no pruebas ejecutadas por este revisor.