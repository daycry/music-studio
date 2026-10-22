# Coordinación y snapshot: revisión del componente, intento 1

0 Critical, 1 Important, 0 Minor. B01: el resultado puede afirmar publicación aunque el bus rechazara el evento tras un commit durable. Corrección TDD autorizada. A/C/D sin defectos nuevos; ninguna aceptación del componente.

## Lente A

**Lente A: 0 Critical · 0 Important · 0 Minor en la unidad U2c. T-06 sigue incompleta; esta revisión no autoriza su cierre.**

Revisión estática del diff de seis archivos, fuentes actuales y evidencias archivadas. Los seis SHA-256 coinciden con `sources-freeze.json`. No ejecuté tests ni modifiqué archivos.

| Tarea → criterio | Resultado | Evidencia y límite |
|---|---|---|
| T-06 → sobre `{id, type, ts, data}`, tipos públicos y keep-alive cada 15 s | ✗ completo / ✓ componente | `apps/server/app/sse.py:349` conserva la proyección pública; `sse.py:508` genera el comentario heartbeat. Falta el transporte que ejecute la cadencia. CA continúa abierto en `tasks.md:230`. |
| T-06 → replay y estado actual cuando expire el buffer | ✗ completo / ✓ componente | `apps/server/app/queue/events.py:64` conserva replay/registro bajo lock. `event_snapshot.py:36` construye el snapshot puro. Faltan lectura WAL autorizada, registro/H compartidos y endpoint. CA abierto en `tasks.md:231`. |
| U2c → orden barrera → commit SQLite → publicación | ✓ | `publication.py:70`, `queue/events.py:235`. Tests con SQLite real y dos hilos propios en `test_publication_coordinator.py:21` y `:48`; comprueban estado durable visible y exclusión durante publicación. |
| U2c → fallo posterior al commit conserva resultado; fallo secundario no oculta el primario | ✓ | `publication.py:79` y `:104`; tests `test_publication_coordinator.py:116`, `:149` y `:246`. Publicador y fallos inyectados explícitamente; no se presentan como transporte real. |
| U2c → feed certificado interno, aislamiento y compatibilidad | ✓ | `sse.py:132`, `:225`, `:250`; emisión tras comprobaciones DB en `queue/events.py:253`. Tests `test_event_snapshot.py:180`, `:203`, `:294`, `:303` y `test_publication_coordinator.py:221`. Certificado interno; no acredita reautorización SQL del replay. |
| U2c → snapshot cerrado, determinista y acotado | ✓ | `event_snapshot.py:19` y `:36`; tests `test_event_snapshot.py:60`, `:80`, `:84`, `:130`, `:135`. Cubren deduplicación, conflictos, 1064 jobs, 17 chunks, límite del frame y confirmación únicamente en `end`. |

| Comprobación transversal | Resultado |
|---|---|
| **(1) Tareas hechas realmente implementadas** | ✓ No se declara T-06 completada: `tasks.md:218`; ambos CA siguen desmarcados. |
| **(2) Alcance y `Archivos`** | ✓ Funcionalmente corresponde a la integración/snapshot prevista en `improvement-plan.md:67` y a los seis archivos autorizados en `prompt-original.txt`. **Matiz:** `tasks.md:224` aún no enumera expresamente los nuevos `publication.py` y `event_snapshot.py`; el scope global los admite mediante `apps/server/`. El pase automático no demuestra por sí solo esta correspondencia. |
| **(3) Tests y cobertura** | ✓ Leídos los tests nuevos. Traza actual de siete archivos completos: **239 PASS**, exit 0, sin skips ni selectores de casos. Cada módulo completo supera 80 %, sin exclusiones; cifras abajo. |
| **(4) Constitución explícita** | ✓ Sin infracción identificada. Escritura permanece en el server (`CONSTITUTION.md:18`); no cierre ficticio (`:33`), cambio de contrato público generado (`:35`) ni decisión contradictoria identificada (`:37`). |
| **(5) Verificación de tareas cerradas** | N/A: ninguna tarea afectada está cerrada. La traza 239 **no sustituye** el comando declarado en `tasks.md:227`: `uv run pytest apps/server -k sse -q`. No lo ejecuté para completar evidencia. |
| **(6) Generados y descripción E2/E3** | N/A para interop: el diff no toca `commands/`, `agents/` ni `hooks/`. No procede ejecutar el exportador. Los límites declarados de U2c concuerdan con el código y ADR-0056. |

Cobertura oficial de **archivos completos**, obtenida de `final-selected/coverage-original.json`, con ramas activadas y `exclude_lines` vacío:

| Módulo | Líneas | Ramas | Combinada oficial |
|---|---:|---:|---:|
| `publication.py` | 91,549 % | 81,250 % | **89,655 %** |
| `event_snapshot.py` | 95,238 % | 90,909 % | **93,750 %** |
| `queue/events.py` | 95,595 % | 91,250 % | **94,463 %** |
| `sse.py` | 96,540 % | 92,308 % | **95,227 %** |

Los RED archivados contienen fallos conductuales: core **4**, barrera/fallos **42**, fallback **3** y certificado nulo **1**, con argv/UTC/exit y fuentes previas. Los errores de importación/fixture no cuentan como RED.

**Gaps de requisitos/constitución: ninguno nuevo en U2c.** Los ✗ de T-06 representan alcance pendiente reconocido, no incumplimientos encubiertos. Se conserva la preocupación original del actor sobre deriva de bytes del test nativo disjunto, calificada por Root como formato con AST idéntico; tampoco se acredita ejecución de 453/801, se elimina el fallo SQL QA2 ni se certifican endpoint, E2E o calidad musical.

## Lente B

**1 defecto Important; 0 Critical; 0 Minor.** Evidencia estática, sin ejecutar código ni tests.

| Criterio | Resultado | Fichero:línea y escenario concreto |
|---|---|---|
| Errores de publicación silenciados | ✗ Important B01 | [publication.py:119](/apps/server/app/publication.py:119), junto con [events.py:135](/apps/server/app/queue/events.py:135). Tras un commit durable, `EventBus.publish()` puede rechazar el evento, ejecutar `mark_gap()` y retornar normalmente. El coordinador devuelve entonces `published=True`, sin error, aunque ningún evento haya entrado en el ring. Ocurre con una proyección pública inválida —por ejemplo, `stage="private/path with spaces"`— o un certificado rechazado. También declara éxito si el bus está apagado. El resultado comunicado al caller contradice la publicación efectiva. |
| Orden commit/publicación y barrera | ✓ | `publication.py:75`, `events.py:249`: sin otros defectos identificados. |
| Certificación, copia y replay interno | ✓ | `sse.py:147`, `events.py:208`: sin otros defectos identificados dentro del alcance autorizado. |
| Snapshot: límites, conflictos y salida completa | ✓ | `event_snapshot.py:19`, `event_snapshot.py:82`: sin defectos identificados. |

Verifiqué los seis hashes congelados y los artefactos: JUnit del productor **239 PASS, cero skips**; cobertura oficial de cada módulo completo **≥80 %, cero exclusiones**. Revisé las preimágenes y evidencias RED funcionales; los fallos de importación/harness quedan separados. Estas comprobaciones no constituyen ejecución independiente del revisor ni aceptación de T-06 completa.

## Lente C

**Sin hallazgos.** Gaps: **0 Critical · 0 Important · 0 Minor**.

Revisión limitada al diff congelado de seis archivos (`scope.diff`); los seis hashes actuales coinciden. El selector marcó C=false, sin motivos automáticos; esta revisión C es suplementaria por la nueva certificación interna y autorización del feed.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin nuevos sumideros; consultas ORM por identidad, sin concatenación SQL | `apps/server/app/queue/events.py:249` |
| Autenticación y autorización | ✓ Certificación tras comprobar User/Song/Job/Attempt, pertenencia, engine y ordinal; feed exige sello, propietario e identidad coincidentes | `apps/server/app/queue/events.py:255`; `apps/server/app/sse.py:149` |
| Sesiones | ✓ El diff no introduce rutas HTTP ni modifica sesiones | `apps/server/app/sse.py:133` |
| Secretos hardcodeados | ✓ Sin credenciales nuevas; el sello es una identidad interna de objeto | `apps/server/app/sse.py:176` |
| Deserialización insegura | ✓ Preflight de tipos JSON antes de deepcopy; DTOs revalidados | `apps/server/app/sse.py:255`; `apps/server/app/event_snapshot.py:23` |
| Path traversal / SSRF | ✓ Sin nuevas operaciones de archivos ni solicitudes de red | `apps/server/app/publication.py:74`; `apps/server/app/event_snapshot.py:36` |
| Filtración y manipulación del feed | ✓ Autoridad separada del sobre mutable; proyección pública cerrada, sin exportar el certificado | `apps/server/app/sse.py:224`; `apps/server/app/sse.py:385` |

Evidencia **estática** y lectura de artefactos del productor; no ejecuté código ni tests. JUnit registra 239 pruebas sin fallos ni skips. Cobertura oficial de archivos completos, líneas+ramas y cero exclusiones: publication 89,655 %, snapshot 93,750 %, events 94,463 %, sse 95,227 %. Los logs RED funcionales quedan separados de fallos de importación/harness.

La conclusión corresponde únicamente a U2c interna. Reautorización del replay e invalidación por borrado/cambio de propietario siguen pendientes y deben resolverse antes de exponer SSE. No acredita T-06 completa ni modifica el fallo histórico SQL QA2.

## Lente D

**Sin hallazgos de rendimiento.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Resultado y evidencia estática |
|---|---|
| N+1 | ✓ `apps/server/app/queue/events.py:248`: conserva las consultas por evento; no introduce consultas dentro de un bucle. |
| Bloqueos evitables | ✓ `apps/server/app/publication.py:65`: barrera síncrona explícita para ordenar commit/publicación, con adquisición limitada a 2 s. No se introduce un caller async de producción. |
| Trabajo repetido | ✓ `apps/server/app/sse.py:149`: revalida por suscriptor, hasta 32; la proyección pública es pequeña y acotada. Sin escenario acreditado de degradación material. |
| Complejidad y volumen | ✓ `apps/server/app/event_snapshot.py:18` y `:65`: deduplicación O(n), ordenación O(n log n), máximo 1064 jobs y 17 chunks. Sin crecimiento cuadrático. |

Lente activada por el patrón `queue` en `apps/server/app/queue/events.py`, según `lens-selection.json`.

Revisados los seis archivos del diff capturado y comprobados sus hashes actuales contra el freeze. Evidencia del productor: JUnit 239/239 y cobertura oficial de cada módulo completo ≥80 %, sin exclusiones. **No ejecuté código, tests ni benchmarks**; este resultado se limita a U2c y no acredita rendimiento de la integración futura ni resuelve SQL QA2.

