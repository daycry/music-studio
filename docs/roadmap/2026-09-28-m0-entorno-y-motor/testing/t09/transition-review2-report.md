# T09 — Transición revisión2/3

A/B/D frescos terminalexit0; selectorCfalseDtrue,18fuentes/scopelimpio/paquetesoriginalesverificados porroot. Lectura estática.0Critical5Important0Minor. R09-T01/T02 escenarios originales corregidos según las treslentes, pendientesQA/adjudicaciónfinal. Cinco defectos nuevos, noreset.

| ID | Grado | Evidencia | Escenario | Estado |
|---|---|---|---|---|
| R09-T03 | Important | A-03,`benchmark.py:428;benchmark_runtime.py:1099` | ObservationTimeout elimina contenedor que comunica conservar/query_same_job. | Pendiente reproducción |
| R09-T04 | Important | A-04/B-03,`benchmark.py:443,455,1247` | Fallo sampler durante shutdown puede publicar complete=true y exit0. | Pendiente reproducción |
| R09-T05 | Important | B-01,`benchmark_coordinator.py:145,146,410` | Snapshot entre publicación de custodia y registro contiene recibo sin muestra, v3_audit_summary_mismatch. | Pendiente reproducción |
| R09-T06 | Important | B-02,`benchmark.py:1125` | finished_session pasa observed_utc str como now al validador que exige datetime/Fraction; AttributeError en relectura legítima. | Pendiente reproducción |
| R09-T07 | Important | D-03,`benchmark_coordinator.py:409,426;benchmark_runtime.py:830` | Auditoría transmite historial completo repetidamente;48000episodios superan64Mi caracteres y cada60Mi demanda≈52429RPC. | Pendiente reproducción |

Originales [A](transition-review2-a.md),[B](transition-review2-b.md),[D](transition-review2-d.md). Reproducir/rebatir antescorrección; próxima revisión3/3 finalregular, QA/GPUdespués. IncidenteCLIanteriorlimpiezahistóricanoacreditada preservado; nuevaspruebasCPUno la sustituyen. No160GPU/calibración/spillcero/T09/M0aceptados.
