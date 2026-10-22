# ADR-0064 · Verificación funcional y cobertura tras calibrar la instrumentación

- **Estado:** aceptada bajo delegación del propietario; ejecuciones y QA pendientes.
- **Fecha:** 2026-10-09.
- **Relacionada:** [ADR-0063](ADR-0063-procedencia-en-resolucion-completa-tras-routing.md).

## Problema y evidencia

La unidad de compatibilidad sintética tiene una ejecución completa de 600 casos
con cobertura: 599 correctos y un fallo del caso original de 801 trabajos, cuyo
plazo sigue siendo 10 segundos. Esa ejecución permanece roja.

Una comparación posterior del mismo caso, sin wrappers de diagnóstico, conservó
las 116 fuentes, los parámetros, las aserciones, el heartbeat y los contadores
funcionales. Ambas ejecuciones pasaron: el testcase duró 9,693 s con cobertura
y 2,870 s sin ella. El tiempo del testcase incluye otras fases y no representa
la duración exacta del wait. Los namespaces y UUID de las fixtures difieren.
La comparación demuestra un coste asociado a la instrumentación en esas dos
observaciones; no identifica un mecanismo exclusivo ni garantiza rendimiento
general. La evidencia original y su verificación se conservan en
`.cache/dev-cycle/m1/t05-synthetic-compatibility-unit1/root-trace-comparison-adjudication.json`.

La configuración del proyecto exige TDD, revisión y un mínimo de cobertura del
80 %. El plugin `custom-agents` 1.22.0 exige medición oficial y verificaciones
verdes. La unidad conserva además su guarda más estricta: cada uno de los ocho
módulos completos debe alcanzar el 80 % combinado de líneas y ramas, sin
excluir código. Medir la temporización bajo tracing en todos los casos fue
una condición añadida por el harness, no un criterio funcional del producto.

## Alternativas y decisión

1. Mantener los 600 casos instrumentados como única evidencia. Conserva el
   harness, pero mezcla el comportamiento temporal con el coste medido de
   observación. No justifica ampliar plazos, cambiar el heartbeat o insistir
   en reejecuciones hasta obtener un verde casual.
2. Separar la verificación funcional completa de la medición de cobertura,
   con fuentes congeladas y conjuntos de pruebas explícitos. **Elegida.**

Se requieren **ambas** ejecuciones nuevas y verdes:

- Suite funcional completa de los 600 casos, sin tracing ni wrappers. Incluye
  el caso original801, su plazo de 10 s, todos sus contadores y aserciones,
  sin deselect, skip ni xfail añadidos.
- Ejecución oficial de cobertura de los ocho módulos completos, con líneas
  y ramas, cero exclusiones de código y mínimo del 80 % por módulo. Ejecuta
  los 599 casos restantes; la única selección de instrumentación omitida es
  el parámetro801 del test temporal ya ejecutado en la suite completa. Los
  parámetros200 y400 y todos los demás casos se conservan. El número y la
  identidad de los casos seleccionados se comprueban en colección y JUnit.

Los conjuntos y la configuración efectiva se registran antes de ejecutar.
La cobertura no se usa como prueba del rendimiento temporal; la suite sin
traza no acredita cobertura. Las fuentes de producto y pruebas deben ser
idénticas entre ambas ejecuciones y mantenerse congeladas hasta la revisión.
Un cambio posterior exige repetir la evidencia afectada.

## Guardas de aceptación

No se combinan los 599 pases históricos con un focal para inventar una suite
verde. No se reutiliza la cobertura de la ejecución roja como nuevo gate
verde ni se unen trazas históricas. Un error de la ejecución de cobertura
sigue siendo un error, aunque el porcentaje supere el mínimo.

La revisión independiente comprueba esta separación, los conjuntos completos,
los resultados reales y las fuentes. QA reproduce ambas ejecuciones y mantiene
los restantes gates de integración, Docker y producto. La decisión no acepta
la unidad, no cierra T-05 y no reduce el alcance del roadmap.

Otros tests con límites temporales no se excluyen por inferencia. Cualquier
ampliación necesita su propia calibración y decisión explícita; no se adopta
una excepción general para pruebas lentas o fallidas.

[ADR-0067](ADR-0067-verificacion-vigente-del-esquema-sql-con-suite-completa.md)
extiende explícitamente esta separación al conjunto SQL vigente de32 suites,
con colección1056/1055, cuatro módulos completos y suplemento Linux de los
tres skips originales. La extensión conserva el mismo parámetro801 y su
plazo; no declara una calibración causal nueva del source SQL ni una
excepción general de instrumentación.
