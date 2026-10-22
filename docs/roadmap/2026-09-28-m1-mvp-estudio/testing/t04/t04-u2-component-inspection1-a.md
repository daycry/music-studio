**Lente A: 0 Critical · 1 Important · 0 Minor.** Revisión limitada a **T-04/U2, inspección de componente 1**. No concede aceptación de T-04, U3 ni del hito.

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Tareas hechas realmente implementadas | ✓ Sin cierres indebidos | `tasks.md:173,183–190`: T-04 en progreso, ocho CA abiertos. |
| Alcance y `Archivos` | ✓ | `tasks.md:177,771`: cola, integración main/dispatcher y cinco tests expresamente previstos. Diff de 12 archivos; admission intacto. |
| Tests y cobertura actual | ✗ Falta cubrir la continuidad después de offload | `test_dispatcher_retry.py:75`: verifica presupuesto/modos, pero no el siguiente cambio de engine. Gap A-U2-01. |
| Constitución explícita | ✓ Sin infracciones adicionales identificadas | `docs/CONSTITUTION.md:18–22,33,35`: persistencia server, contrato, capacidades, residencia única y estado del ledger. El gap bloquea el despacho; no demuestra dos modelos residentes. |
| Verificación de tareas cerradas | No aplica | T-04 no está completada. La traza de componente no sustituye su Verificación contractual. No la he ejecutado. |
| Generados y descripciones E2/E3 | No aplica a interop | El diff no toca `commands/`, `agents/` ni `hooks/`. No cambia contratos API/schema/health. |

**T-04 → criterios de aceptación.** ✓ indica conformidad de la parte inspeccionada; todos siguen abiertos en el ledger.

| CA | Resultado U2 | Fuente/test |
|---|---|---|
| Carriles, prioridad/FIFO, `not_before`, CPU | ✓ Conservados; U1 previamente aceptado | `admission.py:103,117,157,253`; `test_dispatcher_admission.py:262,280` |
| Protocolo `EngineBackend` y HTTP `/v1` | ✓ | `runtime.py:117,122,156,184,273`; `test_dispatcher_lifespan.py:20` |
| Cadena generación → post.audio → beats | ✗ Pendiente fuera de U2; no gap de esta entrega | `runtime.py:1`; `tasks.md:185` |
| Resolver por tarea verificada | ✓ Conservado y revalidado para retry | `runtime.py:299,309`; `test_dispatcher_retry.py:75` |
| Descarga y VRAM antes de cambiar engine | **✗ A-U2-01** | `runtime.py:318,328`; `dispatcher.py:97,101,145` |
| NDJSON, cursor, efectos y bus | ✓ | `events.py:26,65,90,105`; `test_dispatcher_events.py:14,99,114` |
| Retry durable, presupuesto y offload único | ✓ Reserva y límites; continuidad afectada por A-U2-01 | `retry.py:31,87,125`; `test_dispatcher_retry.py:15,75,151,184` |
| Recuperación durable y cancelación | ✓ Parte U2; ✗ continuación CPU/manual/variantes pendientes | `runtime.py:122,134,175,184`; `test_dispatcher_recovery.py:90,110,155`; `test_dispatcher_cancellation.py:13` |

**A-U2-01 — Important: el retry a offload pierde la residencia y bloquea el siguiente engine.**

En [runtime.py:328](../../../../../apps/server/app/queue/runtime.py:328), `_retry()` carga el modelo sin registrar `dispatcher.resident`. Previamente, el cambio BF16→offload descarga el modelo y deja esa residencia en `None` ([dispatcher.py:145](../../../../../apps/server/app/queue/dispatcher.py:145)).

Escenario: generación GPU → `VRAM_EXCEEDED` durable → retry offload → terminal → job GPU para otro engine. El dispatcher observa el modelo offload cargado, lo considera residencia desconocida y rechaza el despacho antes de descargarlo. Incumple el CA de [tasks.md:187](../../../../../docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:187).

**Sonda propia ejecutada, exclusivamente en memoria, con backends controlados:**

```text
retry offload preflight= True resident= None unloads= 1
next engine preflight= False resident= None unloads= 1
control actual resident preflight= True unloads= 2
```

La prueba existente de offload no detecta esto: su backend `load()` devuelve el acuse sin conservar la residencia, y no prueba un despacho posterior (`test_dispatcher_recovery.py:43`; `test_dispatcher_retry.py:75`).

Cobertura recalculada desde `coverage-original-data` contra fuentes actuales, coincidente con `coverage-final.json`: main **96,59 %**, admission **94,58 %** —intacto—, dispatcher **88,96 %**, events **96,30 %**, retry **92,31 %**, recovery **96,00 %**, cancellation **94,12 %**, runtime **87,55 %**; **cero exclusiones**. Fuentes y copias congeladas coinciden; 76 protegidos sin drift.

Evidencia de entrega contrastada: **324 PASS, 2 skips** en una traza actual; **2 controles HTTP suplementarios separados**. SQLite es nativo; engine/HTTP son sintéticos. Los RED originales conservan argv, UTC y JUnit; los primeros lifespan con fixture incompleta siguen cualificados y no acreditan una historia TDD perfecta. No reejecuté la suite ni modifiqué archivos o ledger.