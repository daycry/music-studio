**Lente B: 1 gap Important.** Revisión exclusivamente estática de las nueve fuentes INLINE; sin herramientas ni ejecución propia.

| Criterio | ✓/✗ | Resultado |
|---|---|---|
| Petición y opciones tipadas, identidad e inmutabilidad | ✓ | Sin defectos adicionales identificados. |
| Coherencia de estado, cursor e identidad del terminal | ✓ | Correspondencia validada entre intento, terminal y cursor. |
| R04-S01: timestamp ausente | ✓ | Corregido: SQL/helper/snapshot exigen `ts` persistido. |
| Validez del timestamp persistido | ✗ | SQL admite fechas imposibles que Pydantic rechaza al leer. |
| Snapshots, soporte, procedencia y colisiones | ✓ | Sin otros defectos identificados. |
| Migración aditiva y fixture histórica | ✓ | Baseline conservado y ciclos actuales separados. |

| Gap | Severidad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| R04-B02 | **Important** | `apps/server/app/migrations/job_attempt_invariants.py:220` | Insertar mediante SQL un intento `failed`, con terminal coherente y `ts="2026-02-30T00:00:00Z"`, supera la comprobación: SQLite acepta/normaliza esa fecha y `datetime(...) IS NOT NULL` resulta verdadero. Al recuperar el terminal, `validate_contract` (`:77`) lo valida como `Event` y Pydantic rechaza el día imposible. La lectura ORM y la proyección del snapshot fallan sobre una fila admitida por las guardas SQL. Los tests nuevos cubren ausencia, texto inválido y offsets, pero no fechas imposibles. |

**Critical: 0 · Important: 1 · Minor: 0.** Esta es evidencia adicional sobre la validación de fechas; no reproduce el defecto corregido de `ts` ausente.

Los ✓ expresan ausencia de otros defectos identificados estáticamente. No emito conformidad A ni aceptación técnica: T04 continúa `en-progreso`, con ocho CA abiertos; QA y wheel/Docker siguen pendientes.