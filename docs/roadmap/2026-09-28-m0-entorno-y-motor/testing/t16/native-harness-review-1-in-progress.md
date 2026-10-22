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

## Puertas pendientes

C seguridad y D rendimiento siguen pendientes. QA independiente del nuevo harness y un preflight fresco deben terminar antes de `--execute`. La revisión no autoriza por sí sola GPU ni cierra T-16/M0. Root corroboró hashes del baseline, candidato y nueve fuentes productivas; no se repite el QA del producto sin cambios.
