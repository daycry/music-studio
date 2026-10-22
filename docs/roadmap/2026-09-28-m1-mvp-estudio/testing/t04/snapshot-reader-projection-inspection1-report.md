# Proyección del lector — revisión de componente 1

A/B/C/D: 0 Critical · 0 Important · 0 Minor. FullSQL/801 y QA pendientes; no aceptación T04 ni speedup declarado.

## Lente A

**Lente A: 0 Critical · 0 Important · 0 Minor.** Sin defectos de requisitos o constitución en el componente revisado. **No supone aceptación completa de T-04.**

Revisado el diff completo de los tres archivos contra el plan, el ledger, el brief y las fuentes actuales. Los tres SHA-256 coinciden con `sources-freeze.json`.

Para esta revisión, **✓ significa conformidad del cambio acotado**; los criterios completos de T-04 continúan pendientes.

| T-04 → criterio de aceptación | Resultado y evidencia `fichero:línea` |
|---|---|
| Carriles GPU1/CPU2, prioridad/FIFO, `not_before`, CPU sin descarga GPU | ✓ Se conservan filtros, orden, elegibilidad y reserva: `admission.py:53`, `:121`, `:186`, `:333`. Tests conservados: `test_dispatcher_scanning.py:661`, `:702`, `:719`. |
| Comunicación mediante `EngineBackend` y adapter `/v1` | ✓ Sin modificación de protocolo ni adapters. El cambio de resolver se limita al snapshot: `resolver.py:33`, `:54`, `:58`. No acredita nuevamente todo el contrato. |
| Cadena generación → post → beats y referencias bloqueadas | ✓ Sin cambios en la cadena; dependencias y referencias del writer permanecen idénticas: `admission.py:264`, `:268`, `:271`, `:276`. |
| Selección por tarea verificada y catálogo en caché | ✓ `Resolver` conserva su AST completo: `resolver.py:112`. El snapshot comparte exactamente los 17 campos anteriores: `resolver.py:33`. |
| Descarga del engine residente y comprobación de memoria | ✓ Fuera del código modificado; se conserva el test de entrada inválida sin descarga: `test_dispatcher_scanning.py:627`. Sin acreditación GPU real adicional. |
| NDJSON, reenganche, progreso, telemetry y bus SSE | ✓ Sin cambios en esos consumidores. La proyección mantiene todas las columnas y sus procesadores, incluida telemetry: `admission.py:226`; prueba de error antes del writer: `test_dispatcher_scanning.py:110`. |
| Reintentos retryable y offload | ✓ `retry.py`, `runtime.py` y `test_dispatcher_retry.py` permanecen byte a byte protegidos. El original 801 queda pendiente sobre esta entrega. |
| Recuperación durable, reconciliación, reintento manual y batch/serie según I-01 | ✓ No se altera su autoridad: writer y reserva idénticos, `admission.py:264`, `:292`. El cierre completo, incluida I-01, sigue pendiente: `tasks.md:190`. |

| Control transversal | Resultado |
|---|---|
| Tareas declaradas terminadas | ✓ T-04 está `en-progreso`, con sus ocho CA abiertos: `tasks.md:171`, `:183`. No hay cierre ficticio en esta entrega. |
| Alcance y `Archivos` | ✓ Los tres archivos corresponden a cola/resolver/tests declarados en `tasks.md:177` y a la decisión conservadora de `tasks.md:1606`. `scope.json` recoge tres archivos dentro del alcance y ninguno fuera. |
| Tests del comportamiento cambiado | ✓ Leídos sus escenarios y aserciones: lector sin entidades (`test_dispatcher_scanning.py:20`), fallback por estado y entre páginas (`:43`), conversiones JSON (`:110`), canon tipado (`:147`) y revalidación de los 17 campos (`:205`). |
| Cobertura actual | ✓ WHOLE oficial, líneas+ramas: **admission 93,3333 %**, **resolver 89,0830 %**, ambos con **cero exclusiones**. Contrastados comando, JSON y datos crudos actuales. No se usa promedio ni cobertura histórica. |
| TDD | ✓ RED funcional original: `red/command.json:1`, exit **1**, UTC **02:22:51**; JUnit y salida muestran lector `Job > 0` frente a `[]`, con writer ya válido. GREEN posterior: exit **0**, UTC **02:25:13**. Los errores privados de fixture no se cuentan como RED. |
| Verificación realmente ejecutada | ✓ Evidencia original de la selección acotada: **271 PASS, 0 FAIL/ERROR/SKIP**, exit **0**, comando y JUnit en `selected-custody-complete/`. **No equivale** a la Verificación completa declarada en `tasks.md:179`; T-04 permanece abierta, por lo que no corresponde el gap «verificación declarada sin evidencia». |
| Constitución explícita | ✓ Sin infracciones de autoridad SQLite/WAL, carriles, cierre con verificación o contratos: `docs/CONSTITUTION.md:18`, `:20`, `:33`, `:35`. La optimización interna no contradice documentación vigente (`:37`). |
| Generados y documentación E2/E3 | **No aplica interop:** el diff no toca `commands/`, `agents/` ni `hooks/`. No cambia contratos públicos; la decisión vigente describe todas las columnas tipadas y fallback ORM. |

**Comprobaciones propias ejecutadas:** hashes, comparaciones AST en memoria y lectura de cobertura SQLite en modo solo lectura. Confirmé writer idéntico, restantes métodos de Admission/Resolver intactos, las 21 funciones originales del test conservadas y cuatro archivos protegidos sin cambios. No ejecuté suites.

**Gaps:** ninguno. Permanecen abiertos los gates completos SQL/801 y QA independiente, el antecedente **1025 PASS / 1 FAIL / 3 SKIP**, y los límites de custodia declarados. No hay evidencia de mejora temporal medida.

## Lente B

**Sin defectos de corrección identificados en el diff acotado.**

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Tipos, conversores y materialización completa | ✓ | `admission.py:224` |
| Cursor y paginación en ambos caminos | ✓ | `admission.py:249` |
| Fallback ORM comprobado en cada página | ✓ | `admission.py:217` |
| Snapshot canónico de los mismos 17 campos | ✓ | `resolver.py:33` |
| Revalidación y autoridad del writer conservadas | ✓ | `admission.py:260` |
| Errores de conversión propagados antes del writer | ✓ | `test_dispatcher_scanning.py:115` |

**Gaps:** 0 Critical · 0 Important · 0 Minor.

Verificación propia ejecutada: hashes del freeze, igualdad con fuentes entregadas y comparación AST del bloque writer. Evidencias de entrega contrastadas: RED funcional previo al código, JUnit actual con 271 PASS y cobertura WHOLE admission **93,3333 %**, resolver **89,0830 %**, cero exclusiones.

Revisión estática y lectura de evidencias; no ejecuté suites. SQL/801 y QA independientes siguen pendientes; este resultado no acepta T-04 ni acredita mejora temporal.

## Lente C

**Sin hallazgos.** Critical: 0 · Important: 0 · Minor: 0.

Alcance: `scope.diff` del componente, tres fuentes actuales cotejadas con `sources-freeze.json`. El selector C dio `false`; Root añadió esta lente para comprobar propietario, visibilidad, JSON y autoridad del writer.

| Criterio | Resultado y evidencia |
|---|---|
| Inyección SQL/comando/plantilla | ✓ Proyección mediante atributos SQLAlchemy y etiquetas internas; no introduce SQL dinámico ni ejecución de comandos. `admission.py:226–243`. |
| Autorización y aislamiento | ✓ Conserva joins y filtros de propietario/canción/visibilidad; el writer consulta nuevamente y compara el snapshot. `admission.py:53–70`, `230`, `264–275`. |
| Autenticación y sesión | ✓ Sin cambios en autenticación. El lector comprueba estado por página y mantiene fallback ORM. `admission.py:217–259`. |
| Secretos hardcodeados | ✓ Ninguna credencial nueva en el diff. |
| Deserialización insegura | ✓ Conserva los procesadores de columnas mapeadas y la serialización JSON canónica; no añade pickle ni evaluación de código. `admission.py:226–252`, `resolver.py:22–63`. |
| Path traversal y SSRF | ✓ El diff no introduce rutas, destinos de red ni cambios en sus validaciones. |
| Integridad entre lectura y escritura | ✓ Ambos caminos usan los mismos 17 campos; la lectura proyectada no autoriza escrituras. `resolver.py:33–63`, `admission.py:264–275`. |

Evidencia **estática** del revisor; no ejecuté suites ni pruebas de explotación. Los artefactos consultados registran 271 PASS, cobertura WHOLE actual de admission **93,3333 %** y resolver **89,0830 %**, ambas con cero exclusiones, y RED funcional previo por carga de `Job` en el lector.

Esto no cierra T-04 ni acredita los gates pendientes de SQL/801, QA independiente o custodia OS.

## Lente D

**Sin hallazgos.** 0 Critical · 0 Important · 0 Minor.

Revisado el diff completo de los tres ficheros contra sus preimágenes; coincide con `scope.diff` y los hashes actuales coinciden con el freeze.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| N+1 | ✓ No introduce consultas por candidato; conserva lectura y revalidación por página de hasta 400 jobs. | `apps/server/app/queue/admission.py:239`, `:266` |
| Bloqueos síncronos nuevos | ✓ La proyección no añade E/S, esperas ni llamadas de red. El bloque writer permanece idéntico por AST. | `apps/server/app/queue/admission.py:217`, `:261` |
| Trabajo repetido evitable | ✓ Mantiene una serialización canónica por candidato y su comparación posterior. Reconstruir 25 atributos y cuatro etiquetas por página no acredita una degradación material. | `apps/server/app/queue/admission.py:226`, `:250`; `apps/server/app/queue/resolver.py:58` |
| Crecimiento con volumen | ✓ Mantiene páginas acotadas y el cursor anterior; no introduce acumulación global ni un nuevo recorrido cuadrático. | `apps/server/app/queue/admission.py:178`, `:213`, `:249` |

Selector D activado por rutas `queue` y `await-en-bucle` en resolver; ese bucle no cambia en este diff.

**Evidencia:** inspección estática y comprobaciones propias de diff, hashes y AST. Artefactos de entrega cotejados: RED funcional por carga de `Job` en el lector; JUnit actual 271 PASS; cobertura WHOLE admission **93,3333 %**, resolver **89,0830 %**, cero exclusiones. No ejecuté suites ni medí speedup.

El fallo SQL anterior y los gates 801/integración/QA pendientes conservan su estado; esta revisión acotada no acepta T-04.

