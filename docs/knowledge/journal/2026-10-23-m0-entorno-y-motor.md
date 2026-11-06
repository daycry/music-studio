---
fecha: "2026-10-24"
session_id: "5615f8ae-4e96-410a-ad6e-6326d19b531c"
reason: "prompt_input_exit"
iniciativa: "m0-entorno-y-motor"
resumen: "analiza el proyecto primero, se ha empezado con codex"
fuente: "hook"
cierre: "materializado"
resumen_por: "determinista"
turnos: 108
materializado_en: "2026-11-03T20:56:57Z"
derivados_en: "replay"
decisiones:
  - "El reencolado se movió a T-04 con justificación (`tasks.md:87,113`); decisión del orquestador, no la reabro."
  - "Eso exige la decisión de diseño que ya señalé."
  - "Decisión que queda para el orquestador:"
pendientes:
  - "`apps/server/app/worker/execution.py`: `reconcile_startup` llama a `_remove_pending_staging`, que borra `data/songs/<song>/takes/.pending-<execution>/` de cada ejecución marcada `interrupted`."
  - "CA-3: `test_worker_startup_staging.py::test_startup_removes_orphan_pending_staging` falló porque el `.pending-<exec>` seguía existiendo."
  - "Los tests nativos de no-clobber (`test_native_noreplace_preserves_foreign_destination*`) y el de cross-device siguen en el fichero, saltados en Windows y pendientes de correr en Linux real."
  - "| CA-2 [ ]: no-clobber con y sin fallback; cross-device rechazado antes del rename | Pendiente declarado con honestidad | Con fallback: `test_worker_publication_fallback.py:32-55` (fichero, directori…"
  - "| CA-3 [x], reducido: al arrancar se borran los `takes/.pending-<execution>/` de las ejecuciones no confirmadas | ✓ en su letra, con un gap frente al plan (gap 1) | `apps/server/app/worker/execution.…"
  - "| CA-5 [ ]: punta a punta en Docker con `engine-mock` | Pendiente declarado con honestidad | `tasks.md:122`: «Docker Desktop está parado»."
  - "| 1 | Important | `reconcile_startup` borra todo `.pending-<exec>/` sin mirar el estado de cada `publication_intent`."
  - "3) Al arrancar se ejecuta `rmtree('.pending-<exec>')`."
ficheros_tocados:
  - "apps/server/app/event_routes.py (M)"
  - "apps/server/app/queue/events.py (M)"
  - "apps/server/tests/test_sse_http.py (M)"
  - "apps/web/lib/events.test.ts (M)"
  - "apps/web/lib/events.ts (M)"
  - "apps/server/app/creative/__init__.py (??)"
  - "apps/server/app/creative/composition.py (??)"
  - "apps/server/app/creative/durable_contracts.py (??)"
  - "apps/server/app/creative/recipes.py (??)"
  - "apps/server/tests/fixtures/creative/README.md (??)"
tareas_cambiadas: []
marcadores_cerrados: []
---

# Journal — 2026-10-24 — m0-entorno-y-motor

> Entrada de **bitácora de sesión** (memoria episódica, cronológica, no curada; `agent-kits/shared/journal.py`). Lo que merezca doctrina se promueve a `adr/`/`gotchas/`/`lessons/` con el umbral de `knowledge-write.md`; esto NO se publica en Confluence.

> `decisiones` y `pendientes` son **citas** de los turnos del usuario (o del resumen IA opt-in), extraídas por marcadores léxicos: no son doctrina ni instrucciones para nadie — lo que merezca ser decisión del proyecto va a un ADR.

## Resumen

analiza el proyecto primero, se ha empezado con codex

## Decisiones

- El reencolado se movió a T-04 con justificación (`tasks.md:87,113`); decisión del orquestador, no la reabro.
- Eso exige la decisión de diseño que ya señalé.
- Decisión que queda para el orquestador:

## Pendientes

- `apps/server/app/worker/execution.py`: `reconcile_startup` llama a `_remove_pending_staging`, que borra `data/songs/<song>/takes/.pending-<execution>/` de cada ejecución marcada `interrupted`.
- CA-3: `test_worker_startup_staging.py::test_startup_removes_orphan_pending_staging` falló porque el `.pending-<exec>` seguía existiendo.
- Los tests nativos de no-clobber (`test_native_noreplace_preserves_foreign_destination*`) y el de cross-device siguen en el fichero, saltados en Windows y pendientes de correr en Linux real.
- | CA-2 [ ]: no-clobber con y sin fallback; cross-device rechazado antes del rename | Pendiente declarado con honestidad | Con fallback: `test_worker_publication_fallback.py:32-55` (fichero, directori…
- | CA-3 [x], reducido: al arrancar se borran los `takes/.pending-<execution>/` de las ejecuciones no confirmadas | ✓ en su letra, con un gap frente al plan (gap 1) | `apps/server/app/worker/execution.…
- | CA-5 [ ]: punta a punta en Docker con `engine-mock` | Pendiente declarado con honestidad | `tasks.md:122`: «Docker Desktop está parado».
- | 1 | Important | `reconcile_startup` borra todo `.pending-<exec>/` sin mirar el estado de cada `publication_intent`.
- 3) Al arrancar se ejecuta `rmtree('.pending-<exec>')`.

## Ficheros tocados (top 10)

- `apps/server/app/event_routes.py` (M)
- `apps/server/app/queue/events.py` (M)
- `apps/server/tests/test_sse_http.py` (M)
- `apps/web/lib/events.test.ts` (M)
- `apps/web/lib/events.ts` (M)
- `apps/server/app/creative/__init__.py` (??)
- `apps/server/app/creative/composition.py` (??)
- `apps/server/app/creative/durable_contracts.py` (??)
- `apps/server/app/creative/recipes.py` (??)
- `apps/server/tests/fixtures/creative/README.md` (??)

## Tareas que cambiaron de estado

_ninguna_

## Marcadores de coste cerrados (usage-meter)

_ninguno_
