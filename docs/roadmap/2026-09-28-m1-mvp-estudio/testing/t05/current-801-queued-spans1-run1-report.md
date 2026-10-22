> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# MediciÃ³n acotada 801

Resultado: PASS; caso 11.826 s; espera original 9.3987292 s; CPU submit desde espera 9.3985729 s.

Captura nueva: 5576 archivos fÃ­sicos. Gaps de mÃ³dulos cargados: 0; faltantes entre los 59 anteriores: 0. Deltas de fuentes: 0.

SÃ³lo una ejecuciÃ³n. Causa original UNKNOWN; sobrecoste total del observador UNKNOWN sin control pareado. TDD n/a: mediciÃ³n sin implementaciÃ³n. SQL histÃ³rico 1025 PASS / 1 FAIL / 3 SKIP preservado. No aceptaciÃ³n de SQL/WHOLE/T05/M1/M0â€“M5.

| Etiqueta | Fase | Hilo | llamadas | inclusivo s | propio s |
|---|---|---|---:|---:|---:|
| queued.Session.close | deadline | executor0 | 2 | 3.95E-05 | 3.95E-05 |
| queued.Session.close | deadline | executor1 | 1 | 1.56E-05 | 1.56E-05 |
| queued.Session.flush | deadline | executor0 | 8 | 4.13E-05 | 4.13E-05 |
| queued.Session.flush | deadline | executor1 | 4 | 1.53E-05 | 1.53E-05 |
| queued.SessionTransaction.__exit__ | deadline | executor0 | 2 | 0.0079866 | 2.29E-05 |
| queued.SessionTransaction.__exit__ | deadline | executor1 | 1 | 0.0009255 | 1.05E-05 |
| queued.SessionTransaction.close | deadline | executor0 | 2 | 0.0001152 | 0.0001152 |
| queued.SessionTransaction.close | deadline | executor1 | 1 | 4.69E-05 | 4.69E-05 |
| queued.SessionTransaction.commit | deadline | executor0 | 2 | 0.0079637 | 0.007834 |
| queued.SessionTransaction.commit | deadline | executor1 | 1 | 0.000915 | 0.0008611 |
| queued._dependencies | deadline | executor0 | 800 | 0.0015859 | 0.0015859 |
| queued._dependencies | deadline | executor1 | 2 | 1.16E-05 | 1.16E-05 |
| queued._eligible | deadline | executor0 | 800 | 0.0020262 | 0.0020262 |
| queued._eligible | deadline | executor1 | 2 | 1.18E-05 | 1.18E-05 |
| queued.after_commit | deadline | executor0 | 2 | 1.45E-05 | 1.45E-05 |
| queued.after_commit | deadline | executor1 | 1 | 7E-06 | 7E-06 |
| queued.current_page.scalars | deadline | executor0 | 2 | 0.0234496 | 0.0234411 |
| queued.current_page.scalars | deadline | executor1 | 1 | 0.01579 | 0.0157861 |
| queued.nested.execute | deadline | executor0 | 4 | 0.0726203 | 0.0726115 |
| queued.nested.execute | deadline | executor1 | 2 | 0.0320771 | 0.0320744 |
| queued.next | deadline | executor0 | 2 | 5.1748828 | 0.0510521 |
| queued.next | deadline | executor1 | 2 | 0.1009868 | 0.0020268 |
| queued.parents | deadline | executor0 | 2 | 0.0158767 | 0.0011611 |
| queued.parents | deadline | executor1 | 1 | 0.0171958 | 0.0003608 |
| queued.preload_references | deadline | executor0 | 2 | 0.0003512 | 0.0003512 |
| queued.preload_references | deadline | executor1 | 1 | 5.4E-06 | 5.4E-06 |
| queued.result.materialize.next | deadline | executor0 | 804 | 2.097692 | 2.097692 |
| queued.result.materialize.next | deadline | executor1 | 4 | 0.0314799 | 0.0314799 |
| queued.scalar_result.materialize.next | deadline | executor0 | 802 | 2.8724865 | 2.8724865 |
| queued.scalar_result.materialize.next | deadline | executor1 | 3 | 0.0102505 | 0.0102505 |
| queued.snapshot_reader.execute | deadline | executor0 | 2 | 0.0443645 | 0.0443483 |
| queued.snapshot_reader.execute | deadline | executor1 | 1 | 0.0080035 | 0.0079976 |
| queued.writer.lock_update | deadline | executor0 | 2 | 0.0579919 | 5.95E-05 |
| queued.writer.lock_update | deadline | executor1 | 1 | 0.0152788 | 2.55E-05 |

El residual queued propio incluye snapshot, sorted, selecciÃ³n y cÃ³digo sin seam; no es coste exclusivo de comparaciÃ³n. Los tiempos anidados son inclusivos y no deben sumarse como categorÃ­as disjuntas. Las instantÃ¡neas host sÃ³lo dan contexto; no atribuyen Blender al deadline.

Propuesta futura Ãºnica: revisiÃ³n estÃ¡tica acotada de la categorÃ­a dominante para demostrar repeticiÃ³n realmente innecesaria antes de definir un RED causal. Sin prueba de evitabilidad no se propone cachÃ© ni optimizaciÃ³n; conservar autoridad writer, snapshot WAL, FIFO global, prioridad, CPU2, negativo una vez e invÃ¡lidos no-null fail-closed.

LimitaciÃ³n de auditorÃ­a: inventario __file__ al cierre; mÃ³dulos retirados de sys.modules no acreditados exhaustivamente. Sin captura tardÃ­a ni repeticiÃ³n. AdjudicaciÃ³n exclusiva Root.

Audit completeness: LIMIT_NONCOMPLIANT_EXHAUSTIVE_LOADED_CLOSURE_UNPROVEN. Session-end audit has zero missing bytes; transiently unloaded modules are unproven. Original full test/helper files retain exact byte parity, stronger than AST subset comparison. No dynamic AST parser or second native call used.

Dominant executor0 deadline spans: queued.next 5.1748828 s; scalar materialization 2.8724865 s; result materialization 2.097692 s; residual 0.0510521 s. Writer lock UPDATE 0.0579919 s; flush 0.0000413 s; commit 0.0079637 s; after_commit 0.0000145 s; preload 0.0003512 s. Nested inclusive totals are not additive. Observed bookkeeping 0.005208 s, total observer overhead UNKNOWN. Overflow counters all zero. Repetition avoidability NOT demonstrated.

Private history: capture failed on reserved locked CLI file before Python; preserved original preparer. Audit PS parser extra-parenthesis error occurred after case and before audit execution; preserved original and repaired audit only. Neither is causal RED. No native testcase repeated.
