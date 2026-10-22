# Coordinación y snapshot: revisión del componente, intento 2

A/B/C/D: 0 Critical, 0 Important, 0 Minor nuevos. B01 corregido. QA independiente actual pendiente; no aceptación completa de T-06. Se conservan los resultados y el fallo anterior.

## Lente A

**Lente A — revisión2 del ajuste B01: 0 Critical · 0 Important · 0 Minor nuevos.** Conforme al alcance del componente; T-06 permanece abierta.

Revisión estática del diff completo de tres archivos, fuentes actuales, brief, plan, ledger y recibos archivados. Los SHA-256 actuales coinciden con `sources-freeze.json`. No ejecuté tests ni modifiqué archivos.

| Tarea → criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| T-06 → sobre público, tipos y keep-alive de 15 s | ✗ Pendiente de aceptación completa; no se declara cerrado | `tasks.md:230`; `improvement-plan.md:69` conserva routing, cliente y E2E posteriores |
| T-06 → replay y recuperación de jobs activos | ✗ Pendiente de integración; no se declara cerrado | `tasks.md:231`; `publication.py:1` explicita que los escritores todavía deben compartir el coordinador |
| T-06/B01 → confirmar únicamente publicación aceptada | ✓ | `queue/events.py:114–155`: rechazo devuelve `False`; aceptación bajo lock devuelve `True`. `publication.py:116` exige identidad con `True` |
| T-06/B01 → conservar resultado durable y errores | ✓ | `publication.py:119–132`; pruebas en `test_publication_coordinator.py:118`, `:295` y `:349` |
| T-06/B01 → compatibilidad legacy y semántica del contador | ✓ | `queue/events.py:110` conserva retorno `None`; `publication.py:46` documenta batch vacío y contador histórico; prueba de invalidación en `test_publication_coordinator.py:175` |
| Alcance y `Archivos` | ✓ | Los tres archivos están declarados en `tasks.md:224`; corresponden a la integración transaccional del plan `improvement-plan.md:69` y a la corrección autorizada en `tasks.md:1896` |
| Tests y TDD causal | ✓ | Prueba real SQLite/EventBus en `test_publication_coordinator.py:295`: commit durable, ring, resultado, contador y epoch. Los dobles de `:349` se identifican expresamente como tales |
| Constitución explícita | ✓ | Sin infracción identificada de `docs/CONSTITUTION.md:18`, `:33`, `:35` y `:37`; el ajuste no cambia contratos HTTP ni cierra la tarea |
| Verificación de tareas cerradas | N/A | T-06 está `en-progreso`, `tasks.md:218`. No consta aquí la ejecución exacta de `tasks.md:227`; los 246 casos seleccionados no la sustituyen |
| Generados/descripciones E2–E3 | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar `export-interop.py --check` |

**Evidencia archivada comprobada:** RED real a las `05:16:04 UTC`, exit **1**, **3 fallos de aserción y 1 caso válido**; ejecución final a las `05:16:52 UTC`, exit **0**, JUnit **246 tests, 0 failures/errors/skips**. Los fallos de fixture y del finalizador no se cuentan como RED de producto.

Cobertura oficial actual de módulos completos, líneas+ramas, una traza y cero exclusiones: `publication.py` **90,32 %**, `queue/events.py` **94,52 %**, `event_snapshot.py` **93,75 %**, `sse.py` **95,23 %**. Cada módulo supera el 80 %; esto apoya la lectura de las pruebas, sin acreditar integración HTTP/WAL/E2E.

**Gaps:** ninguno nuevo de requisitos o constitución en este ajuste. B01 queda corregido según fuente y regresión archivada; QA independiente y aceptación completa de T-06 siguen pendientes.

## Lente B

**Sin defectos nuevos de corrección en el diff de tres ficheros.** B01 anterior queda corregido dentro del alcance revisado.

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Rechazo, certificado inválido y shutdown no declaran éxito | ✓ | `queue/events.py:124`, `publication.py:116` |
| Fallo tras commit conserva valor durable y errores | ✓ | `publication.py:119` |
| Confirmaciones parciales y batches vacíos tienen semántica explícita | ✓ | `publication.py:46`, `publication.py:109` |
| Aceptación protegida por lock; retorno legacy `None` conservado | ✓ | `queue/events.py:110`, `queue/events.py:121` |
| Regresiones causales con SQLite y EventBus reales | ✓ | `test_publication_coordinator.py:296` |

**Gaps: 0 Critical · 0 Important · 0 Minor.**

Revisión estática, sin ejecutar código ni tests. Hashes actuales coinciden con el freeze. Artefactos originales comprobados: RED funcional de tres fallos y un caso válido; JUnit final de 246 PASS; cobertura oficial WHOLE de los cuatro módulos ≥80 %, cero exclusiones. Los doubles y errores del harness quedan separados de esa evidencia.

Este resultado no acredita QA independiente ni aceptación completa de T-06.

## Lente C

**Sin hallazgos de seguridad introducidos o reabiertos.** Gaps: **0 Critical · 0 Important · 0 Minor**.

Revisado el diff completo de tres archivos capturado en `t06-coordinator-snapshot-inspection2/scope.diff`, frente a las preimágenes de la entrega. Los SHA-256 actuales coinciden con `sources-freeze.json`.

| Criterio | Resultado y evidencia — fichero:línea |
|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin nuevos sumideros. `publication.py:116` invoca el bus; el SQL añadido en `test_publication_coordinator.py:328` es literal de prueba. |
| Autenticación y sesión | ✓ El diff no modifica sesiones ni añade acceso HTTP. `queue/events.py:114` incorpora un método interno. |
| Permisos/autorización | ✓ Conserva la validación del certificado antes de insertar en el ring (`queue/events.py:139`) y el filtro de suscriptores (`queue/events.py:149`). |
| Secretos hardcodeados | ✓ Sin credenciales nuevas; los identificadores de `test_publication_coordinator.py:307` son datos de prueba. |
| Deserialización insegura | ✓ Conserva el preflight de tipos y límites antes de `deepcopy` (`queue/events.py:129`). Sin nuevas cargas pickle. |
| Path traversal | ✓ Sin operaciones nuevas de filesystem en producción. La ruta de prueba deriva de `tmp_path` (`test_publication_coordinator.py:301`). |
| SSRF | ✓ Sin llamadas de red ni destinos controlables añadidos (`publication.py:115`, `queue/events.py:114`). |
| Confirmación y errores | ✓ Requiere `True` por identidad (`publication.py:116`); rechazo o error conserva el valor durable e intenta invalidar el feed (`publication.py:119`). `publish` legacy conserva retorno `None` (`queue/events.py:110`). |

C fue **suplementaria**: el selector capturado devuelve `lente_c=false`, sin motivos; Root añadió la revisión por certificación y autorización internas.

Evidencia del revisor: **inspección estática y lecturas**, sin imports, pruebas ni mutaciones. Los recibos archivados muestran RED real con SQLite/EventBus **3 fallos + 1 aprobado** y GREEN **246 aprobados**; no son ejecuciones independientes mías. Este resultado no acepta T‑06, su integración HTTP/SSE ni cierra el B01 de la lente B.

## Lente D

**Sin hallazgos de rendimiento.** 0 Critical · 0 Important · 0 Minor.

Alcance: diff de los tres archivos capturado en `t06-coordinator-snapshot-inspection2/scope.diff`, contrastado con la preimagen del fixture Git y las fuentes actuales; hashes coincidentes con el freeze.

| Criterio | Resultado | Fichero:línea y evidencia estática |
|---|---|---|
| N+1 | ✓ | `publication.py:115`: la confirmación no añade consultas por publicación. |
| Bloqueos síncronos nuevos | ✓ | `queue/events.py:124`: conserva el lock existente; el acuse no añade esperas ni E/S. |
| Trabajo repetido evitable | ✓ | `publication.py:116`: añade una comprobación booleana y un incremento por evento; no duplica validación, copia ni serialización. |
| Crecimiento con volumen | ✓ | `queue/events.py:147`: conserva el recorrido por suscriptores, limitado a 32. Para 1064 publicaciones, mantiene el mismo orden de trabajo previo; el contador ocupa espacio constante. |
| Compatibilidad legacy | ✓ | `queue/events.py:109`: delega una vez; no publica dos veces. |

Activación automática: ruta `apps/server/app/queue/events.py`, patrón `queue`, según `lens-selection.json`.

Revisión exclusivamente estática y de lectura. Los recibos archivados acreditan 246 PASS y cobertura WHOLE sin exclusiones superior al 80 %; no ejecuté tests ni benchmarks. Este resultado no acredita mejoras de rendimiento ni cierre de T-06.

