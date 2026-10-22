> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Medición residual actual del caso original [801]

Resultado: [{'name': 'test_global_busy_gpu_negative_once_and_available_cpu_native[801]', 'time_s': 11.515, 'outcome': 'PASS'}]; proceso 28536, exit 0; una ejecución original, sin repetición.

CPU submit desde wait.start: 9.1408055 s (null = no observado). Timeout original 10 s, AST de tests/copias idéntico.

## Agregados del intervalo deadline

| Fase | Clase fija | Calls | Tiempo inclusivo s | Excepciones |
|---|---|---:|---:|---:|
| arbitrate | other | 1 | 9.111256 | 0 |
| arbitrate | queued_cpu | 1 | 0.211719 | 0 |
| arbitrate | queued_gpu | 801 | 1.018861 | 0 |
| arbitrate | retry_cached_negative | 800 | 0.001084 | 0 |
| arbitrate | retry_first_busy | 1 | 0.000371 | 0 |
| canonical | reader | 802 | 0.007138 | 0 |
| canonical | writer | 803 | 0.011451 | 0 |
| contract_event | retry | 801 | 0.017573 | 0 |
| contract_load | other | 809 | 0.007583 | 0 |
| contract_load | retry | 801 | 0.006397 | 0 |
| contract_request | other | 809 | 0.028719 | 0 |
| contract_request | retry | 801 | 0.021485 | 0 |
| hydration | other | 4 | 0.000035 | 0 |
| hydration | queued | 1613 | 4.640951 | 0 |
| hydration | retry | 4 | 2.887509 | 0 |
| merge | other | 3211 | 7.831822 | 0 |
| queued | queued | 4 | 4.881540 | 0 |
| queued_logic | other | 1613 | 0.044679 | 0 |
| retry | retry | 4 | 2.932798 | 0 |
| retry_logic | catalog_miss | 2 | 0.000261 | 0 |
| retry_logic | eligible | 801 | 0.003841 | 0 |
| sql | other | 14 | 0.092441 | 0 |
| sql | queued | 12 | 0.165667 | 0 |
| sql | retry | 1 | 0.024291 | 0 |
| transaction | other | 19 | 0.025501 | 0 |
| transaction | queued | 15 | 0.008269 | 0 |
| transaction | retry | 1 | 0.000002 | 0 |
| transaction | writer | 4 | 0.071554 | 0 |
| type_event | other | 2 | 0.000002 | 0 |
| type_event | retry | 801 | 0.019418 | 0 |
| type_load | other | 2 | 0.000033 | 0 |
| type_load | retry | 801 | 0.008242 | 0 |
| type_request | other | 2 | 0.000139 | 0 |
| type_request | retry | 801 | 0.023389 | 0 |

Contadores fijos: [802, 0, 0, 0, 0, 2, 800, 1, 801, 1, 1, 1, 1, 0, 0, 0]. Índices 0 proyección tipada (snapshot_values, rama efectiva), 1 fallback ORM observado, 4/5 catálogo observado hit/miss, 6/7 retry rechazo cacheado/primera inspección, 8/9 queued GPU/CPU, 10 CPU submit, 11/12 espera start/finish, 13/14 overflow eventos/labels. Índices 2/3/15 reservados, sin afirmación de medición.

Tiempos inclusivos solapados: no sumar como coste exclusivo. Contadores de clases describen el camino observado; first_busy es primera inspección, sin demostrar por sí solo exclusividad del motivo de rechazo. Agregados asignados a la fase al entrar; pueden cruzar el final de wait. Sin control pareado ni medición de CPU exclusiva o sobrecoste total del observador. No se demuestra planificación exclusiva del SO ni causa histórica.

Captura BEFORE física: 8427 archivos; end-loaded UNKNOWN: 5; cierre transitorio descargado UNKNOWN. Guard delta: 0. Managed Python 3.12 alias resuelto al físico. Raw cobertura y JSON actuales seis, líneas sin exclusiones; la cobertura de un caso no acredita >=80 % de suite.

Backend CPU fake original/heartbeat: integración CPU explícita, no prueba GPU. No se omiten validadores, no se cambian requests, prioridades, cache, FIFO, CAS o carriles. No implementación ni extracción de módulos. QA2 FAILED permanece vigente; un PASS aquí no lo sustituye.

Propuesta futura: decidir desde los agregados; coste evitable y equivalencia de una optimización no demostrados. No lazy-validation/cache/rediseño autorizado por esta medición. Una propuesta TDD deberá conservar validación íntegra de request/load/event, identidad congelada, root authority y contrato público, y aportar RED causal antes del cambio.

Incidentes de arnés previos: PowerShell trató stderr del unittest como error terminante; quedó preservado harness-red. Reparación del arnés y directorio red2 anteriores al caso. RED2 privado por assertion count 0 != 2, GREEN posterior. No fallos de producto ni reinicio de hipótesis.

Metadatos modelo/tokens/EUR/horas IA: null, sin originales del proveedor. No aceptación de tarea/calidad/E2E/GPU ni escrituras ledger/ADR/Git.

## Calificación posterior, sin segunda ejecución

Las cinco aparentes lagunas iniciales eran módulos de tests importados desde las copias BEFORE. El mapa inicial sólo indexaba originales. La calificación usa ambas rutas físicas y hashes de los bytes ya copiados: 978 módulos end-loaded acreditados por copia BEFORE; cero lagunas finales de ese conjunto. Las cinco lagunas iniciales y el primer informe/recibo se conservan. No captura retroactiva ni prueba de módulos transitorios descargados.

Límite de instrumentación: hydration/queued agrupa lector tipado y materialización ORM writer; no se puede separar sus tiempos con estos datos. merge agrupa avances/head-fetch y _order. SQL cuenta execute/scalars por stream, sin atribución separada de cada consulta. No se repite el caso para completar esos puntos. FrozenRetryResolver: 2 observaciones cache-miss; cache-hit/frozen-job cero en el camino busy (las etiquetas no prueban optimizaciones).

Dato causal acotado: 801 request + 801 load + 801 event = 2.403 validaciones contractuales retry medidas, 0,0454555 s inclusivos; sus procesadores result_value acumulan 0,051049 s, solapados con validación. Frente a hydration/retry 2,8875091 s y hydration/queued 4,6409511 s, la antigua cifra estática de validaciones no explica por sí sola los spans dominantes de este episodio. Ni el residuo ni el ahorro evitable están demostrados; no se propone lazy-validation, extracción o rediseño.

Custodia y recursos: cero deltas de 8.427 fuentes capturadas y de las fuentes protegidas de Root; configuración coverage.ini byteigual QA2, line-only, cero exclusiones; selected-nodeids sólo801. PID28536 wait exit0 y asserts originales de limpieza ejecutados por PASS. Descendientes OS y recursos ajenos UNKNOWN. JUnit11,515 s es duración whole-case; submitCPU9,1408055 s y wait-return9,1408864 s son del intervalo de espera; no aumentar deadline.

TDD privado: RED2 AssertionError0!=2 y GREEN preservados; primeras incidencias del arnés no son producto RED. La captura completa gestionada precede al Popen original; sólo cuatro ficheros del harness unittest fueron archivados antes de sus invocaciones, su JUnit/PID y closure completo anterior UNKNOWN.

Entrega parcial de aislamiento, sin aceptación: spans reader/writer y heads/order no desglosados, CPUexclusiva/overhead/desplanificación/histórico UNKNOWN; sin rerun para completarlos. Root decide cualquier nueva unidad o cambio.

Precisión desde raw (corrige cifras de ns escritas manualmente en la calificación anterior): validación contractual retry **0,0454548 s** / 2.403 calls; result processors **0,0510492 s**; hydration retry **2,8875088 s**, queued **4,6409509 s**. Datos exactos y solapados, conservados también en receipt.exact_latency_ns_from_raw.
