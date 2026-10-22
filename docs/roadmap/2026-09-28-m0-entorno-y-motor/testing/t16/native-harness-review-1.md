# T-16 — revisión del harness de resolución nativa, intento 1

Revisión privada de configuración: cuatro literales (imagen, runtime, owner y nombre de contenedor) y cabecera. Baseline `e6fd237e…82c`, candidato `5a3bfa6f…aaa3`. Un fichero completo por lente. Scope exit 0, sin avisos ni exclusiones del usuario. Selector C y D activos; las lentes se ejecutan secuencialmente por el límite de agentes disponibles.

## Lente A — conforme

| Criterio | Resultado y evidencia |
|---|---|
| Alcance y TDD | Cuatro cambios revertidos en memoria reproducen el cuerpo previo; AST 3.11 válido. TDD n/a: configuración. |
| Producto aprobado preservado | Nueve fuentes congeladas, imagen `18d94fd…`; revisión A+B+C y QA 314 anteriores leídas, no atribuidas al nuevo harness. CA2 conserva su evidencia; CA3 y CA4 abiertas. |
| Namespace y ownership | Asignaciones AST con ULID sintético confirman runtime nuevo; `mkdir(exist_ok=False)` y log exclusivo. Owner e imagen comprobados por cleanup existente. |
| Guardas y preparación | Cinco dependencias congeladas verificadas; rama prepare real produce `prepared_not_executed`, una toma de 30 s, GPU false. |
| Integración real y QA nueva | Pendientes. No GPU, seis tomas de 90 s ni escucha. |

A fresca: cero gaps Critical/Important/Minor. Verificador Python gestionado exit 0 e inspect de imagen exit 0. Primer intento del comando falló por cp1252; se corrigió sólo el comando a UTF-8. Sin lectura de entradas privadas, `.env`, consulta de conocimiento ni escritura del revisor.

## Lente B — conforme

| Criterio | Resultado y evidencia |
|---|---|
| Delta y compatibilidad | Reversión en memoria exacta, AST válido y cinco dependencias congeladas. Probe CPU de firmas descriptor/preflight/factoría/interceptación sobre imagen inmutable: exit 0, sin Torch padre ni pesos. |
| Namespace | AST confirma runtime, owner/name y montaje asociados; no se usa el runtime histórico. |
| Cleanup | Seis escenarios sintéticos sobre funciones reales: propio, owner incorrecto, imagen incorrecta, job ajeno, timeout de stop y contenedor ausente. |
| Propagación y baseline | Cuatro casos reales de la rama final: exits 1/1/1/0; baseline 1600 admitido y 1601 rechazado con dobles. |
| GPU y calidad | No verificables desde esta revisión CPU. |

B fresca: cero defectos. Python/AST/dobles en memoria, inspect y probe CPU con `--network none` exit 0. Primer probe `-c` falló por quoting de PowerShell; repetido por stdin conforme. Candidato y seis fuentes de imagen permanecen iguales. Sin ejecución del harness completo, GPU, modelos, inputs privados, conocimiento ni modificaciones.

## Lente C — conforme

| Criterio | Resultado y evidencia |
|---|---|
| Extracción AST e imagen | Dos SHA del harness y cinco dependencias congeladas conformes; cuatro cambios invertidos reproducen cuerpo íntegro. Inspect confirma imagen `18d94fd…`, usuario engine y HF/Transformers offline. |
| Confinamiento y ownership | AST con ULID sintético confirma runtime/nombre seguros. Cuatro probes sobre cleanup real: owner, imagen o job ajenos no generan órdenes destructivas; el caso propio utiliza el ID validado. |
| Inyección y secretos | Argumentos separados, sin shell=True; token por entorno y puerto loopback. Cinco montajes, tres readonly. |

C fresca: sin hallazgos, CWE n/a. Dos probes Python gestionado en memoria exit 0, AST 3.11/hashes/argv/metadatos y `4_SYNTHETIC_OWNERSHIP_CASES_PASS`. No importó/ejecutó el harness, leyó `.env`/entradas privadas, consultó conocimiento ni modificó archivos. La activación por `exec` línea 49 se revisó sin extender a una auditoría global.

## Lente D — conforme

| Criterio | Resultado y evidencia |
|---|---|
| Trabajo y complejidad | Reversión byte/AST exacta. Baseline y candidato: un for, un while y 84 llamadas; sin trabajo adicional en bucle. |
| Bloqueos y E/S | Sleep 0,3 s y deadline 40 s conservados; una toma de 30 s y cinco mounts. Namespace nuevo en el mismo workspace, sin copias adicionales. |
| Rendimiento real | No verificado por este despacho CPU; no benchmark, pico VRAM ni inferencia. |

D fresca: sin hallazgos. Probe Python gestionado en memoria exit 0, hashes/delta/reversión/AST 3.11/compilación conformes. Las activaciones por ruta cache y sleep línea 113 no introducen un escenario de carga nuevo. Sin GPU, modelos, red, entradas privadas, conocimiento ni escritura.

## Fusión y siguiente puerta

**A+B+C+D frescas: cero Critical, Important y Minor; sin defectos pendientes ni rebates.** Revisión de un fichero completo por lente, delta real de cuatro literales+cabecera; ejecución secuencial por límite de agentes. Conformidades del producto y harness anteriores conservadas sin atribuir sus tests a este delta. Root revalida baseline, candidato y nueve fuentes productivas actuales.

TDD n/a: configuración privada. La QA independiente del nuevo harness está pendiente, seguida de un preflight fresco antes de `--execute`. No hubo ejecución GPU de este harness. CA3 seis tomas de 90 s y CA4 escucha permanecen abiertas; T-16 y M0 no se cierran.
