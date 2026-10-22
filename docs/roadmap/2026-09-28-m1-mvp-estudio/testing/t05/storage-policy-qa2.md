# T-05: política de preparación del almacenamiento — revisión 2 y QA

Fecha: 2026-10-09. Componente técnico aceptado: política offline **PLAN-ONLY**.
T-05 continúa en progreso; este informe no acredita almacenamiento persistente.

La revisión 1 detectó que los tests rojos iniciales sólo comprobaban la presencia
del módulo. Ese defecto Important se corrigió conservando el histórico,
retirando la implementación y reescribiéndola después de siete ejecuciones RED
conductuales. Los resultados antiguos siguen invalidados como evidencia TDD.

En la revisión 2, las lentes A, B y C leyeron el diff completo y conservaron las
aprobaciones anteriores: **0 Critical, 0 Important y 0 Minor** pendientes.
Sus probes propios de lectura y memoria se distinguen de los tests del productor.

La QA independiente ejecutó una sola batería original de 28 casos:
**28 PASS, 0 FAIL, 0 ERROR, 0 SKIP**, terminal real exit0. La cobertura oficial
del módulo completo `storage.py` es 104/109 líneas + 48/54 ramas =
**152/163 (93,2515 %)**, sin exclusiones. Ruff y formato dieron exit0; el parser
PowerShell no encontró errores y el YAML pasó su comprobación offline.
El wrapper Bash no se ejecutó y Compose tampoco.

Root verificó los 26 archivos del inventario de QA, los 28 casos del JUnit,
el terminal, los contadores oficiales y las cinco fuentes antes/después.
La aceptación y la evidencia detallada están en:

- `.cache/dev-cycle/m1/t05-project-storage-preparation-review2/`
- `.cache/dev-cycle/m1/t05-project-storage-preparation-independent-qa2/`
- `root-acceptance.json` dentro del segundo directorio.

La política rechaza aliases y discos existentes, exige identidad/montaje/UUID
coherentes y devuelve planes sin comandos. **El CLI sigue bloqueado con exit2**:
esas comprobaciones simulables no acreditan custodia por handles ni garantías
del kernel. Quedan pendientes el executor nativo, la provisión del VHDX propio,
su montaje persistente, el preflight real, el arranque, el recorrido completo
de audio y la QA E2E de la aplicación. La decisión de arquitectura sigue siendo
[ADR-0069](../../../../decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md).
