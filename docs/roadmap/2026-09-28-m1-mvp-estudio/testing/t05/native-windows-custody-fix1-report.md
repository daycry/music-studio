> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Fix1 privado — B-01, B-02 y B-03

Entrega concreta para review2 fresca y QA independiente del root. Sólo los tres ficheros autorizados; sin ledger, docs, ADR, Git, medidor ni aceptación. No reset del contador. Modelo/tokens/EUR/horas IA NULL.

**final01: 36 PASS, 0 FAIL/ERROR/SKIP**, originales31 + cinco casos en tres funciones nuevas. Exit0, UUID `81baac8b-d1ce-4605-9251-3c7d2e1f78fa`, PID1716, 2026-10-08T22:37:35.594965+00:00 → 2026-10-08T22:37:51.270013+00:00. Única baseline final tras GREEN; comandos, stdout/stderr, JUnit, copias de fuentes/test/fixture/runner/config anteriores a cada ejecución y recibos nativos en cada fase. Fixture de producto readonly byteexact.

| Módulo completo | Cubiertas/total | Coverage.py oficial | Excluidas |
|---|---:|---:|---:|
| `apps/server/app/worker/custody.py` | 191/212 | 90.09433962% | 0 |
| `apps/server/app/worker/custody_windows.py` | 354/384 | 92.18750000% | 0 |

Sólo dos trazas actuales del mismo UUID: pytest y padre efímero. SHA de runtime comprobado antes del spawn; checkpoint de cobertura guardado ANTES de morir realmente. El padre muerto acredita únicamente las instrucciones ejecutadas hasta ese checkpoint. Workloads importan sólo protocolo, sin atribución falsa de cobertura de custodia. Copias raw anteriores a combine y JSON auto-combine preservadas; no unión histórica/exclusiones/promedios/extracción. `raw-traces-before-combine.json` y `parent-death/child-trace.json` verificadas.

## Causas comprobadas y corrección

- B-01: el segundo contain_unknown escapaba del handler, y una consulta de disposition fallida podía impedir recibo/done. El límite externo de finalización captura errores operativos/de consulta tipados, emite UNKNOWN con resources_returned=false y código privado fijo `finalizer_failure`, sin volver a consultar backend ni copiar mensajes del error. finally señala done. El grupo, writer_ref, finalizador y registro OWNERS siguen retenidos; done es disponibilidad de recibo, no recursos devueltos. No se inventa CLOSED ni se repite contención indefinidamente.
- B-02: done precede la salida real del hilo. wait ahora delega join real a asyncio.to_thread, con plazo operativo+20s de presupuesto finito de limpieza. El event loop sigue cediendo; cancel conserva referencia fuerte en el callable del executor y OWNERS. Un hilo realmente activo al agotarse el presupuesto sigue dando TimeoutError. El test usa barreras reales done-set → caller-yielded-before-release → thread-exit; no reloj monkeypatch ni arbitrarysleep.
- B-03: OpenProcess retornaba antes de _own y las consultas/cierre fallido perdían su referencia. open_identity registra Guard/anclajes en el grupo ANTES de queries; los errores marcan UNKNOWN/cuarentena sin cerrar el número no acreditado ni matar por PID. El helper standalone conserva su resultado raw exitoso y un journal fuerte para guard parcial/fallido; sólo libera duplicados comparados. No cambia el constructor público. GetTimes y mismatch+CloseHandle controlados se prueban sobre objetos OS reales, con nacimiento, referencia kernel de cleanup y witness vivo.

## RED → GREEN

- RED: `test_fix1_repeated_containment_failure_has_finite_unknown_receipt[containment]` falló por done ausente tras **dos** intentos de contención comprobados · 2026-10-08. `red-b01-strengthened`, exit1. La variante disposition también falló por done ausente después de RuntimeError real controlado; GREEN2 en `green-b01-strengthened`. `red-b01` inicial queda preservado; se reforzó causalmente la fixture y se reexpuso únicamente custody.py original owned a la prueba, luego se restauró la propuesta propia. No source histórica se presentó como actual: cada comando guarda su SHA real.
- RED: `test_fix1_done_barrier_waits_actual_thread_exit_without_spurious_timeout` falló con TimeoutError de join(0) sobre un hilo real después de done · 2026-10-08. `red-b02` exit1 → `green-b02` PASS.
- RED: `test_fix1_actual_openprocess_retained_before_identity_fault[get_times/mismatch_close]` falló con grupo sin referencia al OpenProcess real · 2026-10-08. `red-b03` exit1/2FAIL → `green-b03`2PASS. Cleanup RED usó exclusivamente Guard/anclaje kernel del objeto capturado. Witness sobrevivió ambos comportamientos; `injection.json` etiqueta expresamente la inyección finita, NO fallo espontáneo de WinAPI.

Originales de las funciones, asserts, decorators, parametrizaciones, fixtures e imports anteriores conservados por subsecuencia AST exacta (`original31-ast-guard.json`). Tres fuentes before coinciden con review1/final04, no final03. Trece protegidos del mapa root + fixture readonly exactos y cotejos por fase.

## Lint e incidencias

Ruff `checks01` detectó BLE001 del catch genérico inicialmente propuesto; se limitó a errores operativos/de consultas explícitos. `checks02` PASS proyecto para owned3 y fixture readonly, formato PASS; `strict01` PASS **--isolated default** para esos mismos ámbitos, sin --ignore E402 ni edición de fixture/config global. No claim de lint global del repositorio.

Incidente del lector PowerShell del JSON oficial: ConvertFrom-Json no soporta una clave vacía. JSON original intacto; lectura por stdlib json en entrega, sin repetir baseline/combine. No se etiqueta fallo de producto ni RED. Los primeros RED emiten warnings de hilo por el defecto reproducido; final sin warnings de hilo.

`receipt.json`, `actor-command-accounting.json`, `source-current.json`, `scope.diff`, fuentes before/after y `inventory-noncli.json` forman la entrega. Inventario íntegro excluye únicamente cuatro nombres CLI reservados exactos del nivel superior y su propio JSON. No writes a esos cuatro; usage CLI original queda al parent, sin reconstruir tokens.

Review2 y QA independientes pendientes. Sin cierre de T05/M1, Linux, CPU2, audio, SQL, GPU, UI, E2E ni calidad.

DONE_WITH_CONCERNS: review2 fresca y QA independiente pendientes del root; inyecciones nuevas etiquetadas, sin afirmación de fallo espontáneo de WinAPI.
