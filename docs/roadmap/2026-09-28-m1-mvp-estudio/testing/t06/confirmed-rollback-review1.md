# Rollback confirmado · revisión independiente, intento 1

Un gap Important B-01 exige corrección: la limpieza debe garantizarse también ante interrupciones. A/C/D no encuentran defectos en sus lentes. Sin aceptación técnica ni cierre de T-06.

## Lente A

**Lente A: conforme para la unidad ADR-0061 O1. Gaps: 0 Critical, 0 Important, 0 Minor. No acredita el cierre de T-06.**

Revisados el diff completo de los tres archivos congelados, las fuentes actuales, `task-brief.txt`, plan, ledger, constitución y evidencia original de entrega.

| Tarea → criterio | Resultado | Evidencia `fichero:línea` |
|---|---|---|
| T-06 → resultado privado, sellado e inmutable | ✓ | `publication.py:23–33`; test de inmutabilidad en `test_publication_confirmed_rollback.py:387` |
| T-06 → emitirlo únicamente tras rollback y cierre exitosos, antes de intentar commit | ✓ | `queue/events.py:267–309`: cualquier fallo de limpieza impide emitirlo; comenzar commit elimina esa posibilidad |
| T-06 → conservar feed, lectores y DB ante rechazo confirmado | ✓ | `test_publication_confirmed_rollback.py:41–132`: seis rechazos, dump SQLite, epoch, ring, replay, pendientes y lectores de otro propietario |
| T-06 → relanzar el mismo primario y conservar la cola original del traceback | ✓ | `publication.py:119–121`; comprobación de identidad y nodo original en `test_publication_confirmed_rollback.py:168–189` |
| T-06 → errores genéricos, resultados inválidos y transacciones inciertas siguen provocando gap | ✓ | `publication.py:109–131`; tests en `test_publication_confirmed_rollback.py:192–384`, incluido commit que persiste realmente antes del fallo |
| T-06 → conservar validaciones, legacy y B01 | ✓ | `queue/events.py:255–264,311–398`: comparación AST independiente exacta del cuerpo original; confirmación/count intactos en `publication.py:132–154` |
| T-06 → archivos acordes al plan | ✓ | `improvement-plan.md:67–69`; `tasks.md:224,1969`: dos módulos declarados y nuevo test cubierto por `tests`. Scope captura tres archivos, ninguno fuera y ninguna exclusión de usuario |
| T-06 → sobre público y keep-alive de 15 s | ✗ pendiente de aceptación integral | `tasks.md:230`: permanece sin marcar; esta unidad no implementa ni acredita el endpoint completo |
| T-06 → reconexión y recuperación de jobs activos | ✗ pendiente de aceptación integral | `tasks.md:231`: permanece sin marcar; allwriters, WAL, cliente y E2E siguen fuera de esta entrega |
| T-06 → evidencia de Verificación para una tarea cerrada | No aplica al cierre | `tasks.md:218,227`: sigue `en-progreso`; el baseline acotado no sustituye `uv run pytest apps/server -k sse -q` |
| T-06 → principios explícitos de la constitución | ✓ | Sin violaciones introducidas de `docs/CONSTITUTION.md:32,43,56,58,62`; no cambia contrato público, esquema ni autoridad de escritura |
| T-06 → interop E2/E3 | No aplica | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador |

**Evidencia contrastada:** JUnit original registra **271 tests, 0 fallos, 0 errores, 0 skips**, con comando original exit **0**, del **06:20:29 al 06:20:48 UTC**. Los tres hashes actuales coinciden con el freeze y las capturas previas a esa ejecución. Los siete archivos antiguos ejecutados siguen byteexactos.

Cobertura oficial actual de módulos completos, líneas y ramas, en una sola traza RAW verificada y **cero exclusiones**:

| Módulo | Cobertura |
|---|---:|
| `publication.py` | 96,2264 % |
| `queue/events.py` | 95,7143 % |
| `event_snapshot.py` | 93,7500 % |
| `sse.py` | 95,2267 % |

El JUnit RED original confirma **cuatro rechazos causales** antes del cambio productivo: identidad, secuencia, propietario y ordinal. Los errores iniciales de fixtures y los enum inválidos de terminal/replay no cuentan como RED de producto.

El wrapper privado solo introduce metadata sintética y digest `unknown`; no acredita pesos reales ni custodia de modelos. Las inyecciones de fallos están explícitamente identificadas.

**Sin defectos de requisitos o constitución en esta unidad.** Ejecuté únicamente comprobaciones de lectura, hashes y AST; no reejecuté suites ni modifiqué archivos. QA independiente y seguimiento de seguridad permanecen pendientes; el SAST histórico Medium no queda convertido en una auditoría limpia.

## Lente B

**Un defecto Important; ninguno Critical ni Minor.**

| Criterio | Resultado | Fichero:línea y escenario |
|---|---|---|
| Limpieza ante interrupciones | ✗ **B-01 · Important** | [events.py:297](apps/server/app/queue/events.py:297): un `KeyboardInterrupt` durante `_prepare_batch`, después de adquirir el writer SQLite, elude `except Exception` y abandona la sesión sin rollback ni cierre. La transacción puede retener el bloqueo mientras siga referenciada por el traceback. Es una regresión respecto al gestor de contexto legacy. |
| Rollback confirmado y propagación del primario | ✓ | `events.py:299`, `publication.py:120`: confirmación tras rollback/cierre exitosos, fuera del catch genérico; conserva identidad y cola del traceback. |
| Fallos inciertos y resultados inválidos | ✓ | `events.py:292`, `events.py:305`, `publication.py:123`: mantienen la invalidación del feed. |
| Validación y compatibilidad legacy/B01 | ✓ | `events.py:261`, `events.py:311`, `publication.py:131`: sin otros defectos concretos detectados. |

**Prueba ejecutada por el revisor:** métodos actuales extraídos por AST, SQLAlchemy y SQLite exclusivamente en memoria, con interrupción inyectada tras una escritura real. Camino coordinado: `transaction_active=true`, `close_calls=0`; legacy: `false`, `1`. La interrupción fue inyectada; la transacción y el cierre fueron reales.

Evidencias del productor contrastadas sin repetir la suite: 271 PASS, cuatro RED funcionales anteriores al código, fuentes congeladas coincidentes y cobertura oficial completa 93,75–96,23 %, cero exclusiones. Esto no acredita integración HTTP/SSE ni aceptación de T-06.

## Lente C

**Sin hallazgos.** Gaps: **0 Critical · 0 Important · 0 Minor**.

Alcance: diff sellado de tres archivos en `scope.diff`, contrastado con las fuentes actuales y sus hashes. El selector automático no activó C; root la añadió expresamente para revisar VULN-001 y la procedencia del rollback.

| Criterio | Resultado y evidencia estática |
|---|---|
| Inyección SQL/comando/plantilla | ✓ No introduce construcción de consultas, comandos o plantillas con entradas externas. `apps/server/app/queue/events.py:314` |
| Autenticación y sesión | ✓ No cambia autenticación ni sesiones públicas; la nueva `Session` es transaccional de SQLAlchemy. `apps/server/app/queue/events.py:291` |
| Permisos/autorización | ✓ Conserva validaciones de propietario, canción, intento, ordinal e identidad del engine. `apps/server/app/queue/events.py:321` |
| Secretos hardcodeados | ✓ Ninguno introducido en los tres archivos revisados. `apps/server/tests/test_publication_confirmed_rollback.py:43` contiene datos sintéticos |
| Deserialización insegura | ✓ El resultado privado no se deserializa: exige tipo exacto y sello por identidad. `apps/server/app/publication.py:120` |
| Path traversal / SSRF | ✓ No incorpora acceso a rutas ni peticiones de red. `apps/server/app/queue/events.py:291` |
| Rollback / disponibilidad del feed — CWE-703 | ✓ La excepción original se relanza fuera del catch genérico; el resultado confirmado solo se emite tras rollback y cierre satisfactorios, antes de commit. `apps/server/app/publication.py:119`; `apps/server/app/queue/events.py:304` |
| Fallos inciertos | ✓ Begin, rollback, close o commit fallidos conservan la invalidación; resultados inválidos también. `apps/server/app/queue/events.py:294`; `apps/server/app/publication.py:123` |

Evidencia del productor inspeccionada: JUnit **271 PASS**, cuatro RED funcionales genuinos y dos fallos de fixture excluidos del RED. Cobertura oficial de módulos completos: publication **96,2264 %**, events **95,7143 %**, snapshot **93,75 %**, sse **95,2267 %**, sin exclusiones.

La revisión ejecutó únicamente lecturas y comprobaciones de custodia; no reprodujo pruebas. SQLite/bus/lectores reales se distinguen de fallos inyectados y metadatos sintéticos del Catalog. Estos últimos no acreditan pesos reales.

Este resultado no sustituye el seguimiento del hallazgo histórico Medium, la QA independiente ni la aceptación de T-06 o integración HTTP/SSE.

## Lente D

**Sin hallazgos de rendimiento** en el diff sellado de los tres ficheros. Lente D activada por la ruta `apps/server/app/queue/events.py` (`queue`).

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| N+1 introducido | ✓ Sin regresión: conserva las cuatro búsquedas por evento; no añade consultas dentro de bucles. | `apps/server/app/queue/events.py:311` |
| Bloqueos síncronos nuevos | ✓ Conserva la transacción síncrona bajo la barrera existente; no incorpora esperas, red ni E/S de ficheros. | `apps/server/app/queue/events.py:288` |
| Trabajo repetido evitable | ✓ La limpieza recorre exactamente dos operaciones; preparación y serialización no se duplican. | `apps/server/app/queue/events.py:267` |
| Complejidad con volumen | ✓ El resultado confirmado añade comprobaciones O(1), sin recorrer jobs, publicaciones ni suscriptores. | `apps/server/app/publication.py:120` |

**Gaps Critical / Important / Minor: ninguno.**

Revisión estática del diff completo, fuentes actuales y ADR-0061; hashes coincidentes con el freeze. Evidencia del productor inspeccionada, sin reejecutar suites ni medir rendimiento. Este resultado no acredita integración HTTP/SSE ni aceptación de T-06.

