# ADR-0046 — Cápsulas canónicas y auditoría incremental

- **Estado:** aceptada; implementación, revisión y QA pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación autónoma explícita del propietario
- **Ámbito:** M0/T-09, R09-T10 y R09-T13; complementa ADR-0042 y ADR-0045

La tercera revisión encontró que la renovación transporta el historial completo por interfaces de256KiB y que cada segmento vuelve a validar todo el prefijo. El transporte incremental por sí solo no resuelve estos dos problemas. El diseño compara proteger cada archivo y su namespace (O1) con reunir los originales en cápsulas inmutables propias (O2). Se elige **O2**: hace explícita la autoridad de los bytes aceptados y reduce el número de recursos que necesitan protección. La decisión no acredita rendimiento ni ejecución GPU.

Una cápsula contiene los bytes exactos de request, preparación, commit, RAW, progresos, recibo e inventario cerrado, junto a sus anclas externas. Es el original canónico **online**. Debe estar validada y custodiada dentro del plazo original del episodio, antes de anunciar aceptación. Los packs posteriores sólo reúnen cápsulas ya aceptadas; no permiten aceptar tarde. Cada pack cerrado contiene hasta32 intentos y mantiene los límites existentes. Un intento indivisible demasiado grande se rechaza.

La inmutabilidad exige protección nativa comprobada contra escritura, sustitución y borrado, e identidad del objeto abierta y verificada. Hashes cacheados, mtime, watchers o resúmenes suministrados por el caller no bastan. El índice cerrado verifica offsets y tamaños; no extrae ni resuelve rutas arbitrarias. Pérdida de custodia, identidad o pin invalida la autoridad y bloquea acreditación. Los originales sueltos se preservan: una modificación de éstos impide FINAL, aunque no cambie retrospectivamente los bytes de la cápsula protegida aceptada online.

El consumidor mantiene estado canónico y aplica una transición común sólo a bytes y anclas nuevos, con commit atómico de cursor, hash y estado. Renovación, prerequisites y respuestas llevan referencias opacas acotadas a objetos propios vinculados al contexto; el solicitante no elige un trusted root, ruta, prefijo ni fuente de autoridad. La frescura se comprueba con reloj externo actual en cada acreditación. Al reiniciar se valida el prefijo completo una vez y se establece custodia nueva: el sampler permanece independiente y una pausa no se convierte en continuidad histórica.

FINAL lee todos los originales, cápsulas, packs y anclas desde cero y reconstruye la misma semántica sin confiar en el estado incremental. Conserva intentos rechazados, relojes, política v3, diez baseline/diez loaded/diez unloaded, frescura900s,160 outcomes, plazo2s, cadencia2,5s,256KiB para interfaces pequeñas,64Mi caracteres por segmento y1200 por fragmento. No se amplían límites para ocultar crecimiento.

La aceptación requiere RED/GREEN de desbordamiento y relectura acumulativa, equivalencia incremental/FINAL, ataques a inicio/medio/final y custodia nativa real. Una cadena CPU canónica de volumen debe usar proveedores, procesos, anclas, archivos y validadores reales; medirá lecturas pass-through, bytes y pared. Una prueba acelerada no acredita cadencia ni13hGPU. El sampler concurrente y los deadlines se prueban aparte con reloj real. No se cuentan48.000 entradas sintéticas como48.000 episodios canónicos.

V1/V2 permanecen disponibles para interpretar evidencia offline, pero ninguna entrada live los acepta, tampoco con proveedores inyectados. Las pruebas antiguas se preservan antes de migrarlas por caso: lectores usan RAW almacenado, garantías live usan V3 y las guardas prueban rechazo antes de efectos. No se simula seguridad cambiando sólo etiquetas, usando bypass, xfail o exclusiones ocultas. El manual task_manager_v1 sigue vigente.

La revisión siguiente será **intento4**, continuación decidida por el orquestador tras el límite regular de3, sin reset ni deuda aceptada. T09, GPU, calibración y160 siguen pendientes hasta implementación, revisión y QA nuevas. [Opciones originales](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/growth-design-options.md), [migración por caso](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/legacy-migration-manifest.md) y [revisión3](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/transition-review3-report.md).


**Aclaración factual posterior:** la [prueba canónica](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/growth-functional-probe-report.md) rebate el supuesto desbordamiento del frame/prerequisites: éstos ya contienen una referencia acotada. Se conserva como regresión positiva, sin exigir un fallo inexistente. La revalidación de todo el prefijo sí queda reproducida; O2, la autoridad canónica y FINAL independiente permanecen elegidos para resolver ese coste. Esta aclaración conserva la decisión y no acredita implementación.


**Desarrollo de integración:** [ADR-0050](ADR-0050-autoridad-canonica-aislada-del-benchmark.md) fija la autoridad online en proceso propio, lectura por pasos e ingreso prioritario. La ratificación del diseño no acredita implementación, plazos, FINAL ni rendimiento.
