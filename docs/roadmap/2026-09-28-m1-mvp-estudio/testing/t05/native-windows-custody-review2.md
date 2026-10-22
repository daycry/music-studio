# Revisión de dos lentes — intento 2/3: custodia Windows

**0 Critical · 0 Important · 0 Minor.** B01/B02/B03 corregidos; contador e historia conservados. QA independiente pendiente, sin aceptación de T05.

Actualfix1:36PASS, módulos completos90,0943%/92,1875%, cero exclusiones, dos trazas sólo del UUID actual. No mezcla histórica. Fuente3 y fixture actual exactas; los cambios SQL disjuntos no son freeze global.

## Lente A

**Lente A · revisión 2/3: 0 Critical · 0 Important · 0 Minor nuevos.** Sin defectos de requisitos o constitución identificados en fix1. **No acredita el cierre de T-05 ni acepta la unidad antes de QA independiente.**

Revisados el diff correctivo completo, las fuentes actuales, la fixture conservada, el brief y el dictamen anterior. Cotejo ejecutado de solo lectura: las tres fuentes coinciden con el freeze y las copias de final01; fixture SHA-256 `74025c3…` intacta; AST anterior íntegro como subsecuencia, sin debilitar los 31 casos originales.

Las referencias abreviadas corresponden a `apps/server/app/worker/`, `apps/server/tests/test_worker_native_custody.py` y `docs/roadmap/2026-09-28-m1-mvp-estudio/`.

| T-05 → criterio de aceptación completo | Resultado | Evidencia fichero:línea |
|---|---|---|
| Audio-post en Docker Linux, traslado atómico, assets y manifiesto | ✗ Pendiente, correctamente abierto | `tasks.md:211`; esta unidad ejecuta la fixture interna, `custody_windows.py:267` |
| Take `ready`, `song.json` y análisis beats dependiente | ✗ Pendiente, correctamente abierto | `tasks.md:212`; sin integración runtime/SQLite |
| Limpieza exclusiva del intento acreditado y fallo tipado del take | ✗ Pendiente, correctamente abierto | `tasks.md:213`; gate de staging inerte, `custody.py:1` |

Estos pendientes no son gaps de fix1: T-05 permanece `en-progreso` (`tasks.md:198`) y la secuencia del plan contempla custodia antes de publicación/runtime (`improvement-plan.md:64`).

| T-05 → criterio de la corrección acotada | Resultado | Código y test inspeccionados |
|---|---|---|
| B-01: fallo secundario de contención/query entrega recibo UNKNOWN y señala `done`, conservando referencias | ✓ | `custody.py:263`, `:285`; test `:623`. Backend en memoria: comprueba dos intentos, recibo, recursos no devueltos y retención en `OWNERS` |
| B-02: esperar la salida efectiva del hilo sin `join(0)` prematuro ni bloquear el event loop | ✓ | `custody.py:305`; test `:666`. Join acotado mediante `to_thread`; prueba con hilo y barreras reales |
| B-03: retener el objeto OpenProcess antes de consultas de identidad falibles | ✓ | `custody_windows.py:404`, `:460`; test `:717`. Handles/anclajes kernel reales con fallos controlados de GetProcessTimes/CloseHandle |
| Conservar nacimiento suspendido, pertenencia, árbol propio y testigo extranjero | ✓ | `custody_windows.py:233`, `:326`, `:475`; tests `:146`, `:192`, `:379`, `:427` |
| Conservar pipes acotadas, cancelación y UNKNOWN ante transporte o miembros inciertos | ✓ | `custody.py:71`, `:183`; tests `:251`, `:304`, `:335`, `:493`, `:600` |

| Comprobación transversal | Resultado y evidencia |
|---|---|
| Alcance y `Archivos` | ✓ Tres archivos correctivos, cero fuera de alcance. Worker y tests corresponden a `tasks.md:204`, `:1269` y `improvement-plan.md:64`. Scope capturado sin archivos excluidos |
| Tests y cobertura actual | ✓ final01: **36 PASS, 0 errores/fallos/skips**, exit 0. Módulos completos: `custody.py` **191/212 = 90,0943 %**; Windows **354/384 = 92,1875 %**; ambos sin exclusiones |
| Procedencia de cobertura | ✓ JSON oficial y hashes de las dos trazas originales cotejados. Combine exit 0, salida `Combined 2 files`; exclusivamente UUID `81baac8b-d1ce-4605-9251-3c7d2e1f78fa`. Checkpoint del padre antes de su muerte; sin unión histórica |
| TDD causal | ✓ Argv, UTC, SHA, JUnit y fallos funcionales conservados. B-02/B-03 RED sobre preimágenes; B-01 reforzado reexpuso la fuente original antes de restaurar la propuesta. Historia explícita en `tasks.md:1304`, `:1306`, `:1308`; incidentes de import/fixture no cuentan como RED |
| Constitución explícita | ✓ Sin contradicción identificada con `docs/CONSTITUTION.md:18`, `:24`, `:25`, `:33`, `:35`. Sin nueva autoridad SQL, contratos públicos ni rutas externas |
| Verificación de tareas cerradas | ✓ No se cierra ninguna tarea en este diff. Las verificaciones completas de `tasks.md:206` permanecen pendientes; no las ejecuté para suplir evidencia |
| Generados/descriptores E2–E3 | N/A: el diff no toca `commands/`, `agents/` ni `hooks/`; no procede ejecutar export-interop |

**Gaps nuevos de Lente A: ninguno.** B-01/B-02/B-03 conservan su estado formal anterior hasta adjudicación del root; esta revisión aporta evidencia favorable a las correcciones, sin cerrarlos unilateralmente.

La suite y los fallos nativos citados son **evidencia del productor inspeccionada**. Mis comprobaciones fueron de lectura y cotejo en memoria; no repetí suites ni ejecuté procesos nativos nuevos. QA independiente actual, Linux, audio, CPU2, SQLite, filesystem y E2E siguen pendientes.

## Lente B

**Sin defectos nuevos de corrección.** Review2: **0 Critical · 0 Important · 0 Minor**.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| Error secundario de contención o consulta | `apps/server/app/worker/custody.py:263` | Recibo UNKNOWN conservador y `done` garantizado; referencias retenidas. |
| Carrera entre `done` y salida del hilo | `apps/server/app/worker/custody.py:305` | Join real, acotado y delegado fuera del event loop; cancelación conserva custodia. |
| Identidad fallida tras `OpenProcess` | `apps/server/app/worker/custody_windows.py:412` | Referencia registrada antes de consultas; fallos conservan el objeto en cuarentena. |
| Cierre incierto y objetos ajenos | `apps/server/app/worker/custody_windows.py:580` | La incertidumbre conserva UNKNOWN sin acreditar devolución de recursos. |

B-01/B-02/B-03 presentan correcciones suficientes en la fuente inspeccionada; **su cierre queda pendiente de adjudicación del root**.

Cotejados hashes actuales y fixture. Evidencia del productor: **36 PASS**, cobertura completa **191/212 (90,09 %)** y **354/384 (92,19 %)**, cero exclusiones, dos trazas de final01. RED conductuales conservados; B01 usa backend en memoria, B02 barreras de hilos reales y B03 `OpenProcess` real con fallos controlados.

Revisión estática y cotejos de solo lectura; no ejecuté tests ni probes nativos. QA independiente y aceptación de T05/M1 pendientes.

## Lente C

**Lente C, revisión 2: sin hallazgos. Critical 0 · Important 0 · Minor 0.**

Alcance: diff correctivo de tres archivos respecto a review1/final04, fuentes actuales completas y fixture conservada. El selector automático no activó C; root la añadió por sensibilidad de la custodia kernel, handles y entorno del hijo.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin nuevos intérpretes ni construcción ejecutable desde el payload | `custody_windows.py:256`, `:327`; `custody.py:124` |
| Autenticación y sesión | ✓ No introduce endpoints ni modifica autenticación; conserva correlación del protocolo | `custody.py:63`, `:124` |
| Secretos hardcodeados | ✓ Sin credenciales nuevas; entorno interno permitido conservado | `custody_windows.py:288` |
| Deserialización insegura | ✓ Conserva decoder y validación estructural del handshake | `custody.py:124`, `:173` |
| Path traversal | ✓ Conserva resolución dentro del proyecto y entrypoint fijado | `custody_windows.py:256` |
| SSRF | ✓ Ninguna operación de red introducida | `custody_windows.py:404`; `custody.py:305` |
| Permisos y autorización sobre procesos | ✓ Retiene `OpenProcess` antes de consultas fallibles; exige identidad y pertenencia. La contención opera sobre Job/líder acreditados, sin convertir el PID recibido en autoridad de terminación | `custody_windows.py:168`, `:404`, `:456`, `:580` |
| Liberación ante errores | ✓ Frontera secundaria conserva `UNKNOWN`, recibo negativo y referencias; espera al hilo real con plazo finito | `custody.py:263`, `:290`, `:305` |

**Evidencia ejecutada por este revisor:** cotejos de hashes en solo lectura; coinciden las tres fuentes congeladas y la fixture `74025c3…`. Inspeccionados diff, fuentes, veredicto anterior y configuración sin exclusiones.

**Evidencia del productor inspeccionada:** final01, UUID `81baac8b-d1ce-4605-9251-3c7d2e1f78fa`: 36 PASS, cero fallos/skips; cobertura completa `custody.py` **191/212 = 90,0943 %**, Windows **354/384 = 92,1875 %**, cero exclusiones. Dos trazas actuales con hashes coincidentes. B01 usa backend inyectado; B02 barreras de hilos reales; B03 `OpenProcess` real con fallos controlados.

No ejecuté suites ni probes nativos. B01–B03 permanecen pendientes de adjudicación del root; este resultado no acepta T05 ni sustituye la QA independiente.

## Lente D

**Sin hallazgos de rendimiento.** Gaps: **0 Critical · 0 Important · 0 Minor**.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| N+1 | `apps/server/app/worker/custody_windows.py:456` | Sin consultas SQL; el registro del nieto no introduce nuevas búsquedas por volumen. |
| Bloqueos síncronos | `apps/server/app/worker/custody.py:304` | `join` delegado mediante `asyncio.to_thread`, con presupuesto finito; no bloquea el event loop. |
| Trabajo repetido evitable | `apps/server/app/worker/custody_windows.py:427` | Dos duplicados por identidad; coste constante, sin serialización repetida dentro de bucles. |
| Complejidad y retención | `apps/server/app/worker/custody_windows.py:415`, `:439` | Sin degradación nueva demostrable para esta unidad: hijo y nieto. Retención conservadora ante UNKNOWN; los recorridos por miembros ya existían. |
| Finalización ante errores | `apps/server/app/worker/custody.py:270` | Frontera finita, sin contención recursiva ni espera activa añadida. |

Selector D activado por el patrón `worker` en los tres archivos correctivos. Revisado el diff congelado de review2 y cotejados los hashes actuales, incluida la fixture intacta.

**Evidencia estática del revisor**; sin repetir suites ni ejecutar probes nativos. Evidencia del productor comprobada: 36 PASS; cobertura completa actual 191/212 y 354/384, cero exclusiones, dos trazas del mismo UUID.

B-01/B-02/B-03 conservan su estado previo hasta adjudicación del root. Este resultado no acepta T05 ni acredita rendimiento de audio, CPU2 o integración completa.

