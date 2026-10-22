# Rollback confirmado · revisión independiente, intento 2

Las cuatro lentes no encuentran gaps nuevos. B01 queda corregido técnicamente; la aceptación espera QA independiente y el seguimiento del hallazgo de seguridad. T-06 permanece abierta.

## Lente A

**Lente A · intento 2/3: sin gaps nuevos de requisitos o constitución en el diff acumulado de tres archivos.** T-06 continúa abierta; este resultado no acredita su implementación completa.

| Tarea → criterio de aceptación | Resultado | Evidencia |
|---|---|---|
| T-06 → sobre público, tipos y keep-alive cada 15 s | ✗ Pendiente, correctamente declarado | `tasks.md:230`; el componente revisado no completa transporte/endpoint. No constituye un defecto introducido. |
| T-06 → `Last-Event-ID`, replay y recuperación de jobs activos | ✗ Pendiente, correctamente declarado | `tasks.md:231`; integración completa, WAL, cliente y E2E siguen pendientes. |
| T-06 / ADR-0061 → confirmar rechazo únicamente después de rollback y close satisfactorios, antes de cualquier commit | ✓ | `queue/events.py:295`; tests de conservación de BD y lectores en `test_publication_confirmed_rollback.py:236`. |
| T-06 / ADR-0061 → conservar excepción primaria, identidad y traceback | ✓ | `publication.py:125`; assertions de identidad y traceback en el test nuevo:168 y :378. |
| T-06 / ADR-0061 → incertidumbre invalida el feed; no aceptar booleanos, JSON ni sellos inválidos como confirmación | ✓ | `publication.py:111` y :128; tests nuevos:400, :522 y :562. |
| T-06 / B-01 → limpiar ante interrupciones después de adquirir writer | ✓ | `queue/events.py:267` y :297; test nuevo:109 ejecuta preparación y `flush`, y :179 comprueba limpieza **antes** del `finally` privado. |
| T-06 → compatibilidad legacy y regresiones existentes | ✓ | `queue/events.py:255`; siete tests antiguos byteexact, funciones anteriores del test nuevo AST exactas y los 271 IDs previos conservados en orden. |

| Control solicitado | Resultado | Evidencia |
|---|---|---|
| Tareas declaradas completadas | ✓ | T-06 figura `en-progreso` en `tasks.md:218`; no hay cierre atribuido al componente. |
| Alcance y `Archivos` | ✓ | `tasks.md:224` declara ambos módulos y tests; `improvement-plan.md:67` contempla integración transaccional. `scope.diff` contiene únicamente los tres archivos autorizados; hashes actuales coinciden con el freeze. |
| Tests y cobertura actual | ✓ | Lectura de los 614 renglones del test nuevo. JUnit y salida originales acreditan **294 PASS, 0 errores/fallos/skips**. Cobertura WHOLE: publication **96,43 %**, events **95,71 %**, snapshot **93,75 %**, sse **95,23 %**; cero exclusiones, una ejecución. AST con ubicaciones del baseline coincide con las fuentes actuales. |
| TDD conductual | ✓ | RED original del fix: `06:38:22 UTC`, exit 1, `assert 'close' in []`; colección válida. GREEN completo posterior: `06:39:45 UTC`, exit 0. Los errores anteriores de fixture no se contabilizan como RED funcional. |
| Constitución explícita | ✓ | Sin violaciones observadas de `docs/CONSTITUTION.md:31` —escritura exclusiva del server—, :58 —ledger y verificación de cierre— o :62 —contratos code-first—. No cambia un contrato público. |
| Verificación declarada de tareas cerradas | N/A | T-06 está abierta. Los 294 PASS no sustituyen `uv run pytest apps/server -k sse -q`, declarado en `tasks.md:227`. No lo ejecuté para suplir evidencia. |
| Generados/descripciones, E2/E3 interop | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador interop. |

**Gaps:** Critical **0**, Important **0**, Minor **0** nuevos.

El escenario histórico B-01 queda cubierto por el código actual y la evidencia del productor; su historial se conserva. Mi comprobación fue estática y mediante lectura de artefactos, hashes, AST y JUnit: no ejecuté SQL ni repetí la suite. Las pruebas usan SQLite/bus/lectores reales con interrupciones Python inyectadas; no acreditan señales nativas. QA independiente y revisión focal de seguridad siguen pendientes; VULN-001 Medium no queda cerrado por esta lente.

## Lente B

**Lente B — intento 2/3: sin defectos nuevos.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio de corrección | Resultado | Evidencia |
|---|---|---|
| Limpieza ante interrupción precommit; B01 | ✓ Corregido técnicamente | `apps/server/app/queue/events.py:268`: captura `BaseException`, intenta rollback y cierre. Sondeo independiente con SQLite en memoria: tres clases de interrupción revierten la escritura y cierran la sesión. |
| Confirmación exclusivamente antes de commit | ✓ | `apps/server/app/queue/events.py:293`: sólo emite el resultado confirmado después de rollback y cierre exitosos. |
| Fases inciertas invalidan y propagan el primario | ✓ | `apps/server/app/queue/events.py:298` y `apps/server/app/publication.py:111`. |
| Mismo primario y traceback conservados | ✓ | `apps/server/app/publication.py:125`: relanzamiento fuera del catch incierto; identidad y cola original comprobadas en el sondeo. |
| Interrupción al publicar no devuelve éxito durable | ✓ | `apps/server/app/publication.py:145`: marca gap y propaga `BaseException`. |
| Compatibilidad legacy y preparación compartida | ✓ | `apps/server/app/queue/events.py:254` y `:322`: mantiene el camino legacy y las validaciones originales. |

Evidencia de entrega comprobada, **sin repetir la suite**: JUnit con 294 casos y cero fallos; cobertura WHOLE por módulo 93,75–96,43 %, cero exclusiones; AST con ubicaciones idéntico entre baseline y fuentes actuales. RED original causal: `prepare-KeyboardInterrupt` falla por ausencia de cierre (`calls=[]`), antes del arreglo.

El sondeo propio ejecutó SQLAlchemy/SQLite reales con interrupciones Python inyectadas y un bus doble explícito; no acredita interrupciones nativas ni SSE integral. Las fuentes coinciden con el freeze. La aceptación de B01, QA independiente y revisión de seguridad permanecen en Root.

## Lente C

**Sin hallazgos. 0 Critical · 0 Important · 0 Minor.**

Revisión **2 de 3**, limitada al diff acumulado de los tres archivos de `scope.diff`, contrastado con las fuentes actuales y sus hashes congelados. El selector automático no activó C; Root la añadió para revisar VULN-001 y el tratamiento de `BaseException`.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin construcción nueva de consultas, comandos o plantillas mediante entradas externas. | `apps/server/app/queue/events.py:314` |
| Autenticación y sesión | ✓ Sin cambios en autenticación o sesiones públicas. `Session` corresponde a SQLAlchemy. | `apps/server/app/queue/events.py:289` |
| Permisos/autorización | ✓ Conserva pertenencia, bajas, ordinal, identidad del engine y del evento. | `apps/server/app/queue/events.py:320` |
| Secretos hardcodeados | ✓ Sin credenciales introducidas; datos de prueba sintéticos. | `apps/server/tests/test_publication_confirmed_rollback.py:101` |
| Deserialización insegura | ✓ No deserializa el resultado privado; exige tipo exacto y sello por identidad. | `apps/server/app/publication.py:125` |
| Path traversal / SSRF | ✓ No añade operaciones sobre rutas ni peticiones de red. | `apps/server/app/queue/events.py:288` |
| Limpieza ante interrupciones — CWE-703 | ✓ Captura `BaseException` y procura rollback y cierre antes de confirmar el rechazo. | `apps/server/app/queue/events.py:267`, `:297` |
| Incertidumbre y disponibilidad del feed | ✓ Commit intentado o limpieza fallida mantienen gap y propagación; una interrupción de publicación no se convierte en `PublicationOutcome`. | `apps/server/app/publication.py:111`, `:145`; `apps/server/app/queue/events.py:303` |

**Evidencia inspeccionada del productor:** RED funcional `prepare-KeyboardInterrupt` a las **06:38:22 UTC**, fallo `assert 'close' in []`, anterior al cambio; baseline final **294 PASS**, JUnit sin errores. Cobertura oficial completa: publication **96,43 %**, events **95,71 %**, snapshot **93,75 %**, sse **95,23 %**, todas con cero exclusiones. Las diferencias posteriores al baseline son comentarios, con paridad AST registrada.

Esta revisión realizó lecturas y comprobaciones estáticas; **no ejecutó pruebas**. La evidencia del productor utiliza SQLite, bus y lectores reales con interrupciones Python inyectadas; no acredita señales nativas ni pesos reales.

El código actual aborda la causa de B-01 sin borrar su historial. Este resultado no cierra el Medium histórico, la QA independiente, el seguimiento de seguridad ni la aceptación completa de T-06.

## Lente D

**Sin hallazgos de rendimiento.** Critical: 0 · Important: 0 · Minor: 0.

Activación de D: patrón `queue` en `apps/server/app/queue/events.py`, según `t06-confirmed-rollback-inspection2/lens-selection.json`.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| N+1 introducido | ✓ | `apps/server/app/queue/events.py:311`: conserva las cuatro búsquedas por evento; no añade consultas dentro de bucles. |
| Bloqueos síncronos nuevos | ✓ | `apps/server/app/publication.py:108`, `apps/server/app/queue/events.py:288`: conserva la barrera y la transacción síncronas existentes; no añade esperas ni E/S externa. |
| Trabajo repetido evitable | ✓ | `apps/server/app/queue/events.py:270`: limpieza de dos pasos fijos, independiente del número de jobs o lectores. |
| Complejidad con volumen | ✓ | `apps/server/app/publication.py:141`: publicación lineal del batch, con límite existente de 1064; sin recorridos adicionales introducidos. |

Revisión estática del diff acumulado completo y las tres fuentes actuales; hashes coincidentes con el freeze. Evidencia del productor inspeccionada: RED funcional por ausencia de cierre y baseline de 294 PASS. SQLite y bus reales con interrupciones inyectadas en fronteras Python; no prueba de señales nativas. No ejecuté suites ni benchmarks ni modifiqué archivos.

Este resultado corresponde únicamente a la Lente D; no cierra B-01, QA, seguridad ni T-06.

