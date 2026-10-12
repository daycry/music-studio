# QA del componente Windows K2

El componente de adquisición registra y limita sus recursos antes de llamar al sistema. Los errores reconocidos devuelven sus buffers; los errores inciertos mantienen la custodia. El cierre de un ancestro revoca nuevas adquisiciones en todo el subárbol y conserva el cierre ordenado de sus descendientes.

Dos revisiones independientes, en el tercer intento, confirman cero defectos pendientes del componente. Se corrigieron la retención del buffer por una traza de excepción y la revocación incompleta, y se comprobaron los límites UTF16, locator y requested.

QA independiente: **792 pruebas CPU correctas**,16 pruebas deseleccionadas por nombre; JUnit792casos reales adaptado explícitamente a qa-gate, **exit0**, sin fallos, reintentos ni interrupciones. Este resultado corresponde a pytest/CLI; la UI y los E2E del hito siguen pendientes.

Se auditaron cuatro pruebas nativas ROOT actuales con las mismas ocho fuentes: apertura/cierre readonly propios y tres interrupciones. La prueba normal cerró13aperturas; las interrupciones conservaron UNKNOWN local hasta terminar el proceso propio. No se reconsultaron PID históricos.

La unión oficial de cinco capturas Coverage7.16.2 se reprodujo con resúmenes y vectores faltantes idénticos. Cada módulo entero supera80% en líneas, ramas y total, sin exclusiones, medias ni crédito de capturas antiguas.

| Módulo | Líneas | Ramas | Total |
|---|---|---|---|
| storage_journal_windows_abi.py | 90.7865% | 80.9524% | 88.6165% |
| storage_journal_windows_acquisition.py | 93.5542% | 83.7748% | 91.4729% |
| storage_journal_windows_identity.py | 87.9545% | 80.1230% | 85.8407% |
| storage_journal_windows_io.py | 97.0339% | 86.9231% | 94.8505% |

Se verificaron51SHA antes y después,49archivos de entrega y290archivos de soporte. El PDF local tiene6objetos de página y estructura válida; su texto y diseño no fueron inspeccionados por rasterización. Uso real de tokens/coste desconocido.

**T-05 y M1 permanecen abiertos.** Faltan K4b/S1/G1, CREATE y seguridad del objeto creado, sharing bilateral, K5 positivo, concurrencia/matrices nativas completas y la Verificación del worker, manifiestos, publicación, ready, analysis y cleanup. Ningún criterio integral se marca por este componente.
