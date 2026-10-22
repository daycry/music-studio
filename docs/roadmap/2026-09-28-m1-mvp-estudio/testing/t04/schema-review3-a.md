**Lente A: 0 Critical · 0 Important · 0 Minor demostrados en las diez fuentes de esta unidad parcial.** R04-S01 y R04-B02 están corregidos. T-04 continúa `en-progreso`; la aceptación técnica sigue pendiente de QA independiente.

Revisión exclusivamente estática del paquete INLINE completo. No ejecuté herramientas, tests ni verificaciones de hashes. Los resultados de ejecución citados son evidencia aportada.

| T-04 → criterio de aceptación | ✓/✗ | Evaluación |
|---|---|---|
| CA1: carriles, concurrencia, prioridad/FIFO y `not_before` | ✗ Pendiente | Entrega futura explícita; no declarada completa. `tasks.md:183`. |
| CA2: `EngineBackend` y cliente HTTP `/v1` | ✗ Pendiente | No implementados en esta unidad. `tasks.md:184`. |
| CA3: generación → post → beats | ✗ Pendiente | No se afirma construcción ni ejecución de cadenas. `tasks.md:185`. |
| CA4: resolver por tarea verificada | ✗ Pendiente | Reservado para otra unidad. `tasks.md:186`. |
| CA5: descarga y comprobación de VRAM | ✗ Pendiente | Sin implementación ni aceptación GPU. `tasks.md:187`. |
| CA6: consumo NDJSON, cursor y SSE | ✗ Pendiente | Persistir cursor/terminal no acredita consumo, efectos transaccionales ni SSE. `tasks.md:188`. |
| CA7: reintentos y offload | ✗ Pendiente | La relación durable prepara esa política; no la ejecuta. `tasks.md:189`. |
| CA8: recuperación, reconciliación y reintento manual | ✗ Pendiente | Conservación estructural presente; recuperación operativa futura. `tasks.md:190`. |

Los ocho ✗ representan trabajo pendiente declarado, **no gaps ni cierres falsos**.

| Criterio transversal A | Resultado | Evidencia y valoración |
|---|---|---|
| Implementación del alcance parcial | ✓ | `models/__init__.py:447` y `job_attempt_invariants.py:104`: Common, FK, ordinal único, identidad contractual del intento, petición y opciones tipadas/congeladas. Conforme a `ADR-0043:12` y `tasks.md:193`. |
| Alcance y `Archivos` | ✓ | Las diez fuentes corresponden a modelos, migración/helper, snapshots, ambas copias contractuales y tests declarados en `tasks.md:177`. No aparecen tablas SSE/recovery ni ampliaciones de health vetadas por `ADR-0047:14`. |
| Tests de los requisitos parciales | ✓ | Pruebas de roundtrip e inmutabilidad (`test_job_attempt_schema.py:149`, `:499`, `:706`), rechazo SQL/ORM (`:192`, `:250`, `:283`), bulk (`:307`), terminal/cursor (`:340`), null (`:835`) y REPLACE (`:846`). Comprueban comportamiento y conservación de datos. |
| Snapshots y propiedad | ✓ | Cierre/pertenencia y validación en `snapshots.py:46`, `:153`, `:263`; pruebas de colisiones, invalidación, soporte/procedencia, movimiento del padre y backup en `test_job_attempt_schema.py:417`, `:431`, `:544`, `:637`, `:659`. Lotes de 400 en `:719`. |
| Compatibilidad histórica | ✓ | Campo nuevo opcional y ausencia interpretada como `[]` (`snapshots.py:231`, `:563`). Golden legado y copias iguales (`test_job_attempt_schema.py:489`); jobs históricos sin identidad inventada (`:684`). Se distinguen **20→21 tablas exportadas** y **23→24 entidades**. |
| Migración aditiva y fixture histórica | ✓ | `0005_job_attempt.py:12` crea DDL propio; no modifica el histórico. Fixture dirigida explícitamente a `0004` (`test_review_fix3_t02.py:310`), con asserts conservados según custodia. Ciclos actuales vacíos/poblados comprueban `head == 0005` (`test_job_attempt_schema.py:764`). |
| R04-S01: timestamp durable explícito | ✓ Corregido | Exigido en helper (`job_attempt_invariants.py:54`), SQL (`:279`) y ambos snapshots (`song-v1.schema.json:2958`). Regresiones de ausencia, UTC y estabilidad tras lectura/restore/backup en `test_job_attempt_review_fix1.py:32`, `:54`, `:75`, `:98`; wire intacto (`:136`). |
| R04-B02: calendario SQL legible | ✓ Corregido | `_utc_sql` valida calendario, hora y fracción (`job_attempt_invariants.py:162`); aplicado al terminal (`:241`) y Common nuevo (`:305`). Tests rechazan fechas imposibles y comprueban lectura ORM de fechas válidas (`test_job_attempt_review_fix2.py:70`, `:81`, `:91`, `:103`). |
| Constitución explícita | ✓ | Sin violación identificada de escritura exclusiva del server (`CONSTITUTION.md:32`), `/v1` compatible (`:33`), ampliación aditiva (`:39`), confinamiento (`:43`), contratos juntos (`:62`) o fechas UTC (`:64`). |
| Cobertura como apoyo | ✓ Limitado | Cobertura **de módulos completos**, aportada: **99,41 % / 93,51 % / 93,88 % / 100 %**, cero exclusiones. Helper actual **184/196**. No consta porcentaje específico del diff; no lo equiparo a `coverage-gate --changed-only`. |
| Verificación de tareas cerradas | No aplica | T-04 permanece abierta (`tasks.md:171`), sin CA cerradas. La verificación de dispatcher (`:180`) sigue pendiente; los tests parciales no la sustituyen. |
| Interop E2/E3 | No aplica | El diff no toca `commands/`, `agents/` ni `hooks/`. Ambas copias song-v1 se actualizan conjuntamente. |
| Comparación OpenAPI | Omitido | No cambia ninguna spec OpenAPI; los contratos modificados son JSON Schema. |

Evidencia aportada: **89 casos originales + 14 regresiones R04-S01 + 71 R04-B02**; suite BD actual **305 pases y 1 skip**. Tras limpiar únicamente el import de fixture, se repitieron los 71 casos propios; no se afirma una nueva ejecución completa posterior. Se conserva el incidente inicial de caché Ruff y la verificación final sin caché.

**Gaps: ninguno demostrado.** No hay evidencia nueva para reabrir los restantes veredictos anteriores. Wheel/Docker y QA independiente siguen pendientes; esta revisión no acredita dispatcher, aceptación T-04/M1, calidad musical ni resultados GPU.