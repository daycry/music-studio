**Lente B: 1 gap Important.** Revisión estática de las ocho fuentes del paquete inline, sin ejecutar herramientas ni pruebas.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Petición y opciones tipadas, identidad e inmutabilidad | ✓ | Validación contractual y guardas INSERT/UPDATE/REPLACE. |
| Coherencia de estado, cursor e identidad del terminal | ✓ | Se exige correspondencia entre terminal, intento, estado y `last_seq`. |
| Conservación determinista del terminal | ✗ | SQL permite omitir `ts`; al leer se genera una fecha nueva. |
| Snapshots: cierre, soporte, colisiones y compatibilidad histórica | ✓ | Sin otros defectos identificados en el código suministrado. |
| Migración aditiva y fixture histórica explícita | ✓ | DDL nuevo independiente; fixture dirigida a `0004`, con ciclos actuales separados. |

| Severidad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|
| **Important** | `apps/server/app/migrations/job_attempt_invariants.py:220` y `:278` | Insertar por SQL un intento `failed`, `last_seq=4`, con terminal válido pero **sin `ts`** supera las guardas: el esquema de `Event` considera ese campo opcional. Al recuperar la fila, `ContractJSON.process_result_value` (`models/__init__.py:443`) valida el evento y ejecuta el `default_factory` de `Event.ts` (`engine_contract/__init__.py:145`). Cada lectura asigna otra fecha al mismo terminal durable. Dos proyecciones pueden diferir sin cambios en SQLite; en dependencias también cambia el digest de procedencia, y una restauración posterior puede declarar una colisión contra esa misma fila. |

**Critical:** ninguno. **Minor:** ninguno.

Los ✓ indican ausencia de defectos adicionales identificados estáticamente, no aceptación técnica. T04 conserva sus ocho CA abiertos; wheel/Docker y QA independiente siguen pendientes.