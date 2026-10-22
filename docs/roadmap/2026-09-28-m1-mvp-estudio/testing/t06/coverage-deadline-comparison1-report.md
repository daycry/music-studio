> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Comparación controlada de cobertura — diagnóstico parcial

Hipótesis única: la instrumentación exacta de final-official ralentiza materialmente el nodo protegido respecto al mismo source/test/bootstrap sin cobertura, acercándolo o llevándolo más allá del deadline de 10 s.

| Orden | Cobertura | Resultado | JUnit caso (s) | Wall Popen (s) | CPU nativa handle directo (s) |
|---|---|---|---:|---:|---:|
| 1 | ninguna | PASS / exit0 / PID5636 | 3,251 | 5,791696 | 0 |
| 2 | events.py + sse.py exacta | PASS / exit0 / PID27096 | 6,077 | 12,793735 | 0,015625 |

El caso cubierto tarda 2,826 s más (1,869 veces); wall incluye imports, colección, configuración y reporte. JUnit incluye fixture/body/teardown, NO mide entrega CPU tras inicio de deadline. Submit y margen real UNKNOWN. GetProcessTimes devuelve los contadores anteriores para el handle Popen: no son CPU agregada del intérprete/descendientes; esa magnitud queda UNKNOWN. No se deduce carga externa ni causalidad del sistema operativo de estos datos.

La pareja apoya ralentización asociada a instrumentación, pero NO confirma la parte de acercamiento/cruce del deadline ni la causa del fallo original. Ambas pasan, el caso completo cubierto queda en 6,077 s; confianza limitada por una pareja y orden fijo. No hay reproducción del fallo original ni causal RED de producto. No etiqueta flaky. No reciprocal: sin resultado contradictorio ni cercanía observada que justifique dos llamadas extra. Total exacto: dos llamadas al nodo801, ninguna suite453.

Controles: tests/helpers íntegros byte/AST; decorators/asserts/parametrización originales, wait_for10 intacto. Fixture copiada byte exact de final-official; STUDIO_QUEUE_TEST_ROOT crea SQLite diferente desde cero, 801 failed GPU +801 queued GPU +1 CPU, sin dispositivo. Mismos PYTHONPATH, runner, pytest.ini y coverage.ini bytes originales; coverage flags son únicamente los dos módulos y reporte JSON. No observer/profile/submitwrap/clockpatch/doubles nuevos. Paths privados cambian por workspace de manera simétrica. Pycache/UV/temp/pytest-cache/DB privados vacíos antes de cada corrida; no datastore ni source caches reutilizados. Caché de ficheros del OS no controlada; orden uncovered→covered limita causalidad. Entorno de ejecución del proyecto cargado; interpreter/venv existentes, sin uv sync ni instalación.

Snapshots source/test/fixture/config/runner/env previos por corrida, argv/UTC/PID/exit/stdout/stderr/JUnit originales y cotejos posteriores archivados. paired-source-parity y original-current-parity distinguen source causal de protección: mapas existentes sin drift, nuevas fuentes de custodia ajenas no integradas en causalidad. La comparación del mapa broad de root sólo cubre sus paths existentes, no demuestra ausencia de archivos nuevos. No freeze ni reversión ajena. Descendientes nativos/cleanup OS UNKNOWN; Popen.wait terminó ambos handles y los asserts originales de cierre pasan.

Historia intacta: final453=452PASS/1FAIL, nodo12,266s; diagnóstico1 uncovered2,556s PASS; H1 profiler13,383s FAIL intrusivo; H2coverage+observer12,285s PASS/submit9,965652s medido allí. Dos hipótesis previas conservadas, esta es una sola prueba adicional autorizada, sin reset. A01entity.updated no se ejecutó en el nodo observado anterior, job.error formatter sí; ello no descarta todos los demás problemas. Ninguno de esos timings históricos se mezcla como pareja actual. Archivos originales históricos no sobrescritos.

Siguiente propuesta concreta, sin implementación: root puede separar evidencia funcional con cobertura de latencia protegida sin instrumentación; antes de corregir producto, acotar coste real de snapshot/admission para los mismos1603jobs mediante un plan de medición seguro para instrumentación, scheduler nativo y predicados intactos. No excluir cobertura, extraer código, ampliar timeout ni cambiar condiciones. Una aceptación funcional calificada tampoco convierte esta pareja en explicación del timeout453.

TDD n/a: diagnóstico readonly, ninguna función de producto/test nueva. No nuevo RED/GREEN, cobertura80% no aplica a producción cambiada ([]), no QA/review2/T06/fullM1 acceptance. Ledger/docs/Git/goals/conocimiento/medidor reservados a root; sin subagentes/red/install/GPU/UI/PDH/WSL/Ollama/Docker. Métricas reales NULL. Primera lectura CONTINUE por líneas sobrepasó Historial: sección vigente releída separada; no causalidad deducida de historial. Limitación de lectura inicial preservada.

DONE_WITH_CONCERNS: pareja ejecutada y auditable; causa original UNKNOWN, sin fix.
