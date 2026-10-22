# Revisión de dos lentes — intento 2: custodia Linux

**0 Critical · 1 Important · 0 Minor**. B01/B02 corregidos en sus escenarios nativos; B03 requiere corrección: un error al crear el selector de gracia tras TERM omite KILL y las esperas. Revisión3 y QA pendientes; T05 abierta.

## Lente A

**Lente A · revisión 2: 0 Critical · 0 Important · 0 Minor nuevos.** B-01 y B-02 corregidos en los escenarios acreditados. T-05 continúa abierta; este resultado no constituye aceptación ni QA independiente.

| T-05 → criterio de aceptación | Resultado | Evidencia |
|---|---|---|
| Audio-post/FFmpeg, traslado atómico, assets y manifiesto | ✗ Pendiente, declarado correctamente | `tasks.md:211`; esta entrega ejecuta una fixture nativa fija. |
| Take `ready`, `song.json` y análisis beats | ✗ Pendiente, declarado correctamente | `tasks.md:212`; no acredita publicación ni SQL. |
| Limpieza del intento acreditado y fallo tipado del take | ✗ Pendiente, declarado correctamente | `tasks.md:213`; custodia y gate todavía separados del runtime. |

Estos pendientes **no son gaps de la unidad**: `tasks.md:198` mantiene `en-progreso` y las tres casillas permanecen abiertas.

| Criterio de revisión | Resultado | Evidencia fichero:línea |
|---|---|---|
| (1) Implementación frente al estado declarado | ✓ | `tasks.md:1481`: entrega acotada, revisión/QA pendientes, sin cierre de T-05. |
| (2) Alcance y `Archivos` | ✓ | `tasks.md:204`, `improvement-plan.md:64`: backend/supervisor dentro de `worker/`, test y fixture dentro del alcance previsto. Diff completo de cuatro archivos; scope archivado sin archivos fuera de alcance. |
| (3) Tests funcionales | ✓ | `test_worker_native_linux_custody.py:463` y `:562`: comprueban salidas nativas, waits, testigo ajeno y UNKNOWN antes del cleanup auxiliar. JUnit actuales: **26 Linux + 36 Windows PASS**, cero errores/skips. |
| (3) TDD y conservación de regresiones | ✓ con límite histórico | Tres JUnit RED funcionales preceden a GREEN; producción RED coincide con las preimágenes. Las 17 definiciones originales Linux conservan AST; Windows permanece byte exacto. No se retroatribuyen argv/UTC individuales ausentes en los RED tempranos. |
| (4) Constitución explícita | ✓ | Sin violación introducida de `CONSTITUTION.md:18` — autoridad del server—, `:33` —ledger/verificación—, `:35` —contratos— o `:37` —decisiones documentadas—. |
| (5) Verificación de tareas cerradas | N/A | Ninguna tarea se cierra. Las verificaciones generales de `tasks.md:206` siguen pendientes; no las ejecuté para completar evidencia. |
| (6) Generados E2 / documentación E3 | N/A / ✓ | El diff no toca `commands/`, `agents/` ni `hooks/`; interop no aplica. Conserva el contrato de ADR-0057 y la secuencia documentada, sin cambios públicos que requieran regeneración. |

| Hallazgo previo | Estado | Escenario y evidencia |
|---|---|---|
| **B-01 · Important** | **Corregido** | EMFILE después de Popen: `custody_linux.py:173` cierra liveness, espera al supervisor y propaga la causa; conserva el grupo parcial UNKNOWN. Test `:463`; FINAL02 acredita tres procesos terminados, wait del supervisor y testigo ajeno vivo. |
| **B-02 · Important** | **Corregido** | ENOSPC/EIO tras registrar el nieto: `custody_linux_supervisor.py:226` ejecuta cleanup independiente del journal, con líder retenido/WNOWAIT, TERM/KILL y waits hasta ECHILD. Test `:562`; ambos recibos acreditan descendientes terminados y `confirmed=false`. |

Cobertura **WHOLE oficial de líneas+ramas**, UUID `df4f514d-b858-4db3-963a-8ffb373db800`, cero exclusiones:

| Módulo | Cobertura |
|---|---:|
| Fachada protegida `custody.py` | 258/293 = **88,0546 %** |
| `custody_linux.py` | 285/333 = **85,5856 %** |
| `custody_linux_supervisor.py` | 255/318 = **80,1887 %** |

Cotejé **4 fuentes propias + 16 protegidas**, fuentes de ejecución y **55/55 trazas originales/copias**. Los porcentajes individuales de ramas Linux inferiores al 80 % no constituyen un gate separado.

**Gaps nuevos: ninguno.** El historial de revisión 1 conserva sus dos Important; no se reinicia el contador. Evidencia propia del revisor: lectura, hashes, AST, JSON y JUnit archivados. No ejecuté suites, Docker, procesos nativos ni señales. QA independiente de los 62 casos y la misma congelación continúa pendiente.

## Lente B

**Lente B, review2: 1 defecto Important; 0 Critical; 0 Minor.**

| Criterio | Resultado | Fichero:línea y escenario |
|---|---|---|
| B01: EMFILE después de `Popen` | Corregido para el escenario original | `custody_linux.py:166`: cierra liveness, espera al supervisor y conserva UNKNOWN. El recibo actual acredita salida de los tres procesos propios y supervivencia del testigo. |
| B02: journal ENOSPC/EIO | Corregido para ambos escenarios originales | `custody_linux_supervisor.py:104`: deriva a limpieza conservadora. Los recibos actuales acreditan TERM/KILL, waits y ECHILD, con `confirmed=false`. |
| B03: fallo durante la limpieza | **Important** | [custody_linux_supervisor.py:259](/[ruta local]/apps/server/app/worker/custody_linux_supervisor.py:259): después de TERM, crear el selector de gracia puede lanzar `OSError`, por ejemplo ENFILE por agotamiento global de archivos abiertos. Está dentro del `finally`, sin protección adicional: la excepción omite SIGKILL (`:263`), la alternativa por pidfd (`:270`), los waits y la notificación final. El líder y nieto de la fixture ignoran TERM (`worker_custody_linux_child.py:27`); pueden sobrevivir al supervisor pese a conservarse autoridad válida sobre su grupo. |
| Identidades y gate UNKNOWN | Sin defecto adicional identificado | `custody_linux_supervisor.py:232`, `custody_linux.py:330`: líder retenido con WNOWAIT antes de señalizar; UNKNOWN impide retornar recursos. |

B03 procede de **inspección estática**, sin reproducción nativa ejecutada por este revisor. Los escenarios originales B01/B02 quedan corregidos; el historial de review1 se conserva.

Verificados los hashes OWNED4 contra el freeze y los JUnit actuales: Linux26 + Windows36, sin fallos ni skips. Cobertura oficial WHOLE por fuente: 258/293, 285/333 y 255/318; cero exclusiones. Estas evidencias del productor no sustituyen QA independiente ni cierran T05.

## Lente C

**Lente C, revisión 2: sin hallazgos. 0 Critical / 0 Important / 0 Minor nuevos o reabiertos.**

Revisado el `scope.diff` completo de los cuatro ficheros y sus fuentes actuales; los cuatro SHA-256 coinciden con el freeze. Selector: `lente_c=false`, motivos automáticos vacíos. C se añadió como revisión suplementaria por la autoridad sobre PGID, pidfd y referencias ajenas.

Las rutas de la tabla son relativas a `apps/server/`.

| Criterio | Resultado | Fichero:línea y evidencia estática |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ | `app/worker/custody_linux.py:110`; `custody_linux_supervisor.py:66`: ejecutables y fixture fijos, argumentos separados, sin shell ni nuevos intérpretes de entrada. |
| Autenticación y sesión | ✓ | `app/worker/custody_linux.py:91`: validación de sesión conservada; el diff no modifica autenticación. |
| Secretos hardcodeados | ✓ | `app/worker/custody_linux.py:109`; `tests/fixtures/worker_custody_linux_child.py:28`: sin credenciales añadidas; metadatos de procesos benignos. |
| Deserialización insegura | ✓ | `app/worker/custody_linux_supervisor.py:203`: JSON sobre canal privado; sin pickle ni ejecución de objetos deserializados. |
| Path traversal / SSRF | ✓ | `app/worker/custody_linux.py:94`; `custody_linux_supervisor.py:98`: raíz interna y nombres fijos; sin nuevas solicitudes de red ni rutas derivadas de mensajes. |
| Permisos y autoridad de señalización | ✓ | `app/worker/custody_linux_supervisor.py:207`: candidato ajeno permanece fuera de `refs`; `:232`: líder retenido con `WNOWAIT` antes de señales; `:277`: recolección posterior. |
| Reutilización de FD / devolución indebida | ✓ | `app/worker/custody_linux.py:169`, `:326`: conserva `UNKNOWN` y bloquea cierre confirmado; no amplía autoridad sobre descriptores ajenos. |

| Defecto previo | Estado en esta lente | Escenario y evidencia |
|---|---|---|
| B01 — Important | Corrección corroborada | EMFILE después de Popen: `custody_linux.py:166` retira liveness y espera al supervisor. El artefacto FINAL02 registra los tres procesos terminados, testigo ajeno vivo y grupo parcial `unknown=true`, `closed=false`. |
| B02 — Important | Corrección corroborada | ENOSPC/EIO tras registrar al nieto: `custody_linux_supervisor.py:218`, `:226` conducen al cleanup. Ambos artefactos registran TERM/KILL, waits hasta ECHILD, testigo ajeno vivo y `confirmed=false`. |

Leídos los JUnit existentes: **26 Linux + 36 Windows, cero fallos/errores/skips**. Cobertura oficial WHOLE de líneas+ramas: **88,0546 % / 85,5856 % / 80,1887 %**, cero exclusiones; no se interpreta como un gate separado de ramas.

**Evidencia propia:** lectura estática y comprobación de hashes. **Evidencia ejecutada:** artefactos del productor, sin ejecutar pruebas ni procesos nativos durante esta revisión. Las inyecciones controladas no acreditan fallos espontáneos del SO; las limitaciones históricas de argv/UTC permanecen. Este resultado no cierra T05 ni sustituye la QA independiente.

## Lente D

**Sin hallazgos de rendimiento. 0 Critical / 0 Important / 0 Minor.**

Revisado `scope.diff` de review2 y las cuatro fuentes actuales: sus SHA-256 coinciden con el freeze. Selector D activado por el patrón `worker` en las cuatro rutas.

| Criterio | Evidencia fichero:línea | Resultado |
|---|---|---|
| N+1 | `custody_linux_supervisor.py:198` | ✓ No introduce consultas a BD dentro de bucles. |
| Bloqueos evitables | `custody_linux.py:176`; `custody_linux_supervisor.py:273` | ✓ Esperas de contención acotadas a 7 y 5 segundos; no hay evidencia de bloqueo nuevo del event loop. |
| Trabajo repetido | `custody_linux_supervisor.py:97,218,299` | ✓ Journal en nacimiento, registro y cierre; admite un único descendiente registrado. No crece por canción ni por mensaje de audio. |
| Complejidad con volumen | `custody_linux_supervisor.py:207,247,268` | ✓ Referencias autorizadas acotadas a líder y descendiente; no aparece crecimiento superlineal con el volumen del dominio. |

**B01: corregido en el escenario acreditado.** Boundary en `custody_linux.py:166`: retira liveness, espera al supervisor y conserva UNKNOWN. El recibo FINAL02 de EMFILE registra salida de los tres procesos propios en 3,137 s y testigo ajeno vivo.

**B02: corregido en los escenarios acreditados.** `custody_linux_supervisor.py:226` ejecuta contención independiente del journal. Los recibos ENOSPC/EIO registran TERM/KILL, ECHILD, ambos descendientes terminados, testigo ajeno vivo y `confirmed=false`.

Evidencia del revisor: inspección estática y lectura de recibos existentes; sin ejecutar procesos, pruebas ni escrituras. No constituye QA independiente ni aceptación de T05; se conserva el historial de los dos Important anteriores.

