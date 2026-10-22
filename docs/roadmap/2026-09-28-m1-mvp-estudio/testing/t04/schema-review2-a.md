**Lente A: ningún gap Critical/Important/Minor demostrado en las nueve fuentes de esta unidad parcial.** R04-S01 está corregido. T-04 permanece `en-progreso`, con ocho criterios abiertos; esta revisión no acredita aceptación técnica.

Revisión exclusivamente estática del paquete INLINE. No ejecuté herramientas, pruebas ni comprobaciones de hashes.

| T-04 → criterio de aceptación | ✓/✗ | Conclusión |
|---|---|---|
| CA1: carriles, concurrencia, prioridad/FIFO y `not_before` | ✗ Pendiente | No implementado ni declarado completo. `tasks.md:183`. |
| CA2: protocolo `EngineBackend` y cliente HTTP | ✗ Pendiente | Entrega futura explícita. `tasks.md:184`. |
| CA3: generación → post → beats | ✗ Pendiente | No se afirma construcción de cadenas. `tasks.md:185`. |
| CA4: resolver por tarea verificada | ✗ Pendiente | Reservado para siguiente unidad. `tasks.md:186`. |
| CA5: descarga y comprobación de VRAM | ✗ Pendiente | Sin implementación ni aceptación GPU. `tasks.md:187`. |
| CA6: consumo NDJSON, cursor y bus SSE | ✗ Pendiente | La persistencia de cursor/terminal no acredita consumo, efectos ni SSE. `tasks.md:188`. |
| CA7: reintentos y offload | ✗ Pendiente | La relación durable prepara su implementación; no ejecuta esa política. `tasks.md:189`. |
| CA8: recuperación, reconciliación y reintento manual | ✗ Pendiente | Conservación estructural presente; recuperación operativa futura. `tasks.md:190`. |

Estos ocho ✗ reflejan trabajo pendiente declarado, **no defectos ni cierres falsos**.

| Criterio transversal A | Resultado | Evidencia estática |
|---|---|---|
| Implementación del alcance parcial | ✓ | Relación tipada con Common, ordinal único, petición/opciones congeladas e identidad contractual: `models/__init__.py:447`, `job_attempt_invariants.py:104`. Corresponde a ADR-0043:12 y `tasks.md:193`. |
| Alcance y `Archivos` | ✓ | Las nueve fuentes corresponden a modelos, migraciones, snapshots, dos contratos y tests declarados en `tasks.md:177`. El helper implementa las invariantes de la migración. No aparece funcionalidad ajena. |
| Tests de los requisitos parciales | ✓ | Roundtrip e inmutabilidad (`test_job_attempt_schema.py:149`, `:499`, `:706`); SQL estricto y bulk (`:192`, `:250`, `:307`); terminal/cursor (`:331`, `:340`); REPLACE (`:846`). Las aserciones comprueban comportamientos, no solamente existencia. |
| Snapshots, propiedad y conservación | ✓ | Cierre y pertenencia (`snapshots.py:46`, `:153`); validación (`:263`); tests de soporte/procedencia, invalidación, colisiones y backup (`test_job_attempt_schema.py:417`, `:431`, `:544`, `:637`, `:659`). Lotes de 400 comprobados en `:719`. |
| Compatibilidad histórica | ✓ | `job_attempt` opcional; ausencia tratada como `[]` en `snapshots.py:231`, `:563`. Golden legado y comparación de copias en `test_job_attempt_schema.py:489`. No se inventa identidad para jobs históricos (`:684`). **20→21 tablas exportadas** y **23→24 entidades** son magnitudes distintas. |
| Migración aditiva y fixture histórica | ✓ | DDL nuevo independiente en `0005_job_attempt.py:12`. Fixture histórica dirigida explícitamente a `0004` (`test_review_fix3_t02.py:310`); el ciclo actual conserva comprobación de `head == 0005` (`test_job_attempt_schema.py:817`). Custodia aportada declara 37 asserts preservados. |
| Corrección R04-S01 | ✓ | Helper exige `ts` explícito y UTC (`job_attempt_invariants.py:54`, `:78`); SQL lo exige (`:253`); ambos esquemas lo requieren (`song-v1.schema.json:2958`). Regresiones cubren INSERT/UPDATE, helper/ORM/snapshot, fechas inválidas y estabilidad tras lecturas/restauración/backup (`test_job_attempt_review_fix1.py:32`, `:54`, `:75`, `:98`). Wire conserva su default (`:136`). |
| Constitución explícita | ✓ | Sin violación identificada de escritura exclusiva del server (`CONSTITUTION.md:32`), migraciones aditivas (`:39`), confinamiento (`:43`), contratos juntos (`:62`) o fechas UTC (`:64`). No se modifica `/v1` ni se añade persistencia a engines. |
| Cobertura como apoyo | ✓ Limitado | Evidencia aportada de módulos completos: **99,41 % / 93,51 % / 93,72 % / 100 %**, cero exclusiones. **No consta porcentaje específico del diff**; no lo equiparo a `coverage-gate --changed-only`. |
| Verificación de tareas cerradas | No aplica | T-04 sigue abierta (`tasks.md:171`). Su verificación de dispatcher (`:180`) permanece pendiente; los resultados parciales no la sustituyen. |
| Interop E2/E3 | No aplica | El diff no toca `commands/`, `agents/` ni `hooks/`. |
| Comparación OpenAPI | Omitido | Ninguna spec OpenAPI modificada; las dos copias son JSON Schema. |

Evidencia de ejecución **aportada**: 89 casos originales y 14 regresiones nuevas; último resultado declarado **234 pases y 1 skip**, helper **179/191**. Se conservan los ocho fallos históricos anteriores y el incidente inicial de caché Ruff; la comprobación final se declara sin caché.

**Gaps:** Critical: 0 · Important: 0 · Minor: 0. No hay evidencia nueva que justifique reabrir otros hallazgos anteriores. Wheel/Docker y QA independiente siguen pendientes; `technical_acceptance` permanece falso.