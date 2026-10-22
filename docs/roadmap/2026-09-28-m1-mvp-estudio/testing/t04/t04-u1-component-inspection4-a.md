**Lente A · inspection4 de T04 U1 fix3: 0 Critical / 0 Important / 0 Minor.** Sin defectos de requisitos o constitución identificados en los tres archivos revisados. **No acredita T-04 completa**, U2/U3 ni aceptación técnica de U1: siguen pendientes QA independiente y revisión integrada.

Rutas abreviadas: `queue/` = `apps/server/app/queue/`; `tests/` = `apps/server/tests/`; `ledger` = `docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md`.

| T-04 → criterio de aceptación | Resultado acotado | Evidencia fichero:línea |
|---|---|---|
| CA1 · Carriles, prioridad/FIFO, `not_before`, CPU sin descargar GPU | ✓ La corrección mantiene la admisión vigente; screening compartido solo descarta. CA completo abierto. | `queue/dispatcher.py:45`, `queue/admission.py:240`, `tests/test_dispatcher_scanning.py:617`, `ledger:183` |
| CA2 · Protocolo `EngineBackend` y adapter `/v1` | ✓ Sin cambios de contrato ni métodos nuevos del backend. CA completo abierto. | `queue/dispatcher.py:7`, `queue/dispatcher.py:208`, `ledger:184` |
| CA3 · Cadena generación → post → beats | ✓ Permanece explícitamente pendiente; fix3 no declara implementarla. | `ledger:185`, `ledger:721` |
| CA4 · Resolución por tarea verificada y descriptor cacheado | ✓ Resolver preservado; seleccionado vuelve a resolución completa y compara identidad/ruta. CA completo abierto. | `queue/dispatcher.py:166`, `queue/dispatcher.py:170`, `ledger:186` |
| CA5 · Unload y comprobación de VRAM libre | ✓ Screening no autoriza el claim; conserva preflight fresco y reserva transaccional. Dos controles introducen ocupación después del screening. CA completo abierto. | `queue/dispatcher.py:73`, `queue/admission.py:240`, `tests/test_dispatcher_scanning.py:705`, `ledger:187` |
| CA6 · NDJSON, cursor y SSE | ✓ Pendiente U2, sin cierre atribuido a esta entrega. | `queue/dispatcher.py:1`, `ledger:188`, `ledger:721` |
| CA7 · Retry y fallback offload | ✓ Pendiente U2, sin implementación añadida ni aceptación declarada. | `ledger:189`, `ledger:721` |
| CA8 · Recuperación e identidad durable | ✓ Fix3 conserva los fallos posteriores al commit y el staging durable; no los convierte en rechazo preclaim. Recuperación completa pendiente. | `queue/admission.py:259`, `queue/admission.py:330`, `queue/dispatcher.py:196`, `tests/test_dispatcher_scanning.py:545`, `ledger:190` |

| Criterio de revisión | Resultado y evidencia |
|---|---|
| 1 · Tareas hechas realmente implementadas | ✓ T-04 está `en-progreso`, con ocho CA abiertos (`ledger:171`, `ledger:183`). La entrega mantiene ese límite (`ledger:721`). |
| 2 · Alcance y `Archivos` | ✓ Los tres archivos corresponden a cola y tests declarados en `ledger:177`, coherentes con Fase 2 del plan (`improvement-plan.md:39`). Fixture de scope: tres cambios, ninguno fuera de alcance; selector conserva motivos por ruta y contenido. |
| 3 · Tests y cobertura | ✓ Lectura de los 17 casos nuevos: seis carreras de inputs, seis controles postcommit, tres tamaños de screening y dos controles de ocupación sobrevenida (`tests/test_dispatcher_scanning.py:488`, `:545`, `:617`, `:705`). Cobertura oficial **admission 192/203 = 94,58 %; dispatcher 128/145 = 88,28 %**, cero exclusiones por módulo. |
| 4 · Constitución explícita | ✓ Sin contradicción identificada con carriles (`docs/CONSTITUTION.md:20`), residencia/VRAM (`:21`) ni cierre mediante verificación (`:33`). |
| 5 · Verificación ejecutada | ✓ Evidencia archivada: argv/UTC/exit **0**, stdout **206 passed** y JUnit **206 tests, 0 failures, 0 errors**. Es verificación parcial de fix3; no sustituye el comando completo de T-04 ni lo declara ejecutado. Al seguir abierta, no aplica «verificación declarada sin evidencia» por cierre. |
| 6 · Generados y documentación E2/E3 | N/A: el diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar `export-interop.py --check`. No cambia contratos ni decisiones documentadas. |

**Evidencia independiente del revisor:** hashes actuales coinciden con la congelación de inspection4 y el manifiesto final; análisis oficial de `.coverage` sobre fuentes actuales reproduce los porcentajes y cero exclusiones. Los seis RED tienen argv, UTC, exit 1 y fallo funcional en JUnit, con producción anterior al fix.

**Límite:** no ejecuté suites ni sondas de producto. SQLite y staging son nativos en la evidencia de entrega; Catalog, hooks e intercalaciones son sintéticos explícitos. Heartbeat no acredita latencia máxima ni GPU. Se conserva el historial de inspection3 y la revisión integrada formal4 pendiente.

**Gaps:** ninguno.