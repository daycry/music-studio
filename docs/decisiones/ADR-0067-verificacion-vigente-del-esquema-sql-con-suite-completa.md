# ADR-0067 · Verificar el esquema SQL con la suite completa vigente

- **Estado:** aceptada bajo delegación del propietario; ejecuciones y aceptación pendientes.
- **Fecha:** 2026-10-09.
- **Relacionadas:** [ADR-0055](ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md), [ADR-0064](ADR-0064-verificacion-funcional-y-cobertura-con-coste-de-instrumentacion.md) y [ADR-0066](ADR-0066-sincronizacion-con-el-submit-real-en-prueba-de-recuperacion.md).

## Contexto

La QA SQL posterior de32 suites ejecutó1055 casos:1051 correctos, un fallo
del parámetro801 y tres skips Windows. Root no la aceptó. Los cuatro módulos
SQL actuales conservan sus bytes, pero sus porcentajes y pases históricos
no acreditan una verificación nueva. La suite sintética601/600 tampoco
incluye todo el alcance de migración, persistencia y snapshots de esa QA.

El plan independiente conserva1055 IDs originales en orden y añade sólo
la regresión de estado retrasado de ADR-0066. Root comprobó sus artefactos,
manifiestos y los cuatro SHA actuales. Fuente privada:
`.cache/dev-cycle/m1/t05-current-sql-verification-plan1/root-custody-and-method-adoption.json`.

## Decisión

Se aplica al alcance SQL vigente la separación funcional/cobertura de
ADR-0064. Se requieren dos ejecuciones nuevas sobre las mismas fuentes:

- Funcional: las32 suites y1056 casos, sin tracing ni wrappers de diagnóstico.
  Incluye el parámetro801 con su plazo original de10s, heartbeat, contadores
  y todas sus aserciones. No se añaden skips ni xfail.
- Cobertura oficial:1055 casos, omitiendo exclusivamente la instrumentación
  de `test_global_busy_gpu_negative_once_and_available_cpu_native[801]`.
  Los parámetros200/400 y todos los demás casos siguen incluidos. No se
  omite código ni se unen trazas históricas.

Esta extensión se limita a esos manifiestos y al mismo parámetro temporal.
La calibración de ADR-0064 midió coste asociado al tracing source8; no prueba
un mecanismo exclusivo ni una calibración causal del source SQL actual.
Separar la medición evita exigir que la cobertura pruebe rendimiento. La
ejecución funcional completa conserva esa comprobación. Cualquier otro
fallo se mantiene rojo y requiere causa probada antes de repetir.

### Ampliación posterior al diagnóstico QA3 y ADR-0068

La siguiente QA conserva los1056 IDs de las32 suites anteriores e incorpora
la suite nueva `test_dispatcher_identity_drift.py`. Su colección real debe
mostrar que, al retirar únicamente esos nuevos IDs, queda exactamente el
conjunto original en orden. No se fija el total final por una estimación.
La cobertura sigue omitiendo exclusivamente el801 conocido y conserva
todos los casos nuevos; ninguna regresión nueva queda dispensada.

La corrección de ADR-0068 cambia resolver y dispatcher. Su cobertura oficial
se suma a los cuatro módulos SQL: **seis fuentes completas**, cada una con
al menos80% combinado y cero exclusiones de código. Ambos conjuntos usan
los mismos bytes actuales, no una unión de ejecuciones históricas. La
calibración anterior no se presenta como medición causal de ese nuevo scope.

El espejo incorpora únicamente dos dependencias nuevas declaradas: el test
de drift y `scripts/init_env.py` original sellado. El test de persistencia
del token conserva sus destinos temporales y su código; no se copia ni usa
un `.env` real. Los originales QA3 y sus27 fallos permanecen intactos.

Cada archivo SQL completo debe alcanzar80% combinado de líneas y ramas:
`models/__init__.py`, `snapshots.py`, `cpu_publication_invariants.py` y
`0006_cpu_publication.py`. La configuración oficial captura la revisión
Alembic por su ejecución real; si traza revisiones adicionales, las declara
íntegras. No se presenta ese JSON como si contuviera sólo cuatro archivos.
`exclude_lines`, `exclude_also` y las exclusiones de código permanecen vacíos.
No se usa promedio ni cobertura de una suite fallida como gate verde.

## Plataformas y guardas

Los tres skips Windows originales requieren ejecución de los mismos casos
en Linux con fuentes y composición vigentes: los dos casos de symlink del
sink de logging y el rechazo de directorio symlink del snapshot. Sus pases
históricos no acreditan automáticamente los modelos/snapshots actuales.
El suplemento se ejecuta en un contenedor CPU propio después de liberar la
ventana temporal; no usa GPU ni modifica servicios ajenos.

Se registran colección/orden, configuración, fuentes y recursos antes y
después, comandos, UTC, estados terminales, JUnit y cobertura oficial nueva.
El bootstrap conserva asserts y recursos Alembic; sólo confina fixtures a
su namespace. No remapea runtime, autoridad ni expectativas para forzar verde.

Los resultados Windows esperados son1053PASS+3SKIP funcionales y1052PASS+
3SKIP instrumentados, más una deselection declarada801. Los tres casos Linux
son los mismos, sin aumentar el total de casos distintos. Cualquier cambio
de colección o fuente exige adjudicación antes del run siguiente.

Esta decisión define la verificación, no acepta el esquema, U2b, T-05 ni
la publicación real de audio. La QA independiente y los restantes gates
de integración, Docker y producto permanecen.
