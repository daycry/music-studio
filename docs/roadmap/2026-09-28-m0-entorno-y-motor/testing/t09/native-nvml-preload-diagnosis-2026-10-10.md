# Sonda de NVML durante precarga — diagnóstico parcial

La sonda envió una precarga BF16, sin generación. Terminó antes de alcanzar un modelo estable: el monitor detectó un incremento sostenido de memoria compartida y la llamada de carga devolvió HTTP 504. **T-09 sigue abierto**; no se modifica proveedor, calibración ni tolerancia.

El orquestador comprobó 22 artefactos del inventario, las 456 lecturas originales y nueve hashes de fuentes. Recibo: `.cache/dev-cycle/t09/native-nvml-load-probe-20261010/root-verification.json`, exit 0 a las 19:14:33 UTC. El informe privado completo, RAW, recibos de procesos y logs están en esa carpeta; el inventario sellado antecede al recibo del orquestador.

## Qué demuestra

| Comprobación | Resultado observado |
|---|---|
| Lecturas en reposo / durante carga | 10 / 446 |
| Lecturas con modelo estable | 0 |
| NVML v1 frente a v2 | `v1.used = v2.used + v2.reserved` en todas las lecturas |
| Memoria reservada | 284 MiB constantes |
| Máximo delta PDH dedicada frente a NVML v2 | 13,2578125 MiB |
| Máximo delta PDH dedicada frente a CLI | 15,203125 MiB |
| Desacuerdos dedicados superiores a 128 MiB | Ninguno en esta ventana |
| Parada del muestreo | `sustained_shared_risk` |
| Retorno de la única precarga | HTTP 504, confirmado por log original acotado |

Usar directamente el campo `used` de NVML v1 como sustituto de CLI introduciría aquí un desacuerdo incluso en reposo. La diferencia de campos está probada; la latencia como explicación del desacuerdo histórico **no está probada**. Las consultas son secuenciales y no representan una captura atómica de todos los proveedores.

La memoria compartida es agregada del adaptador. Su aumento no atribuye desbordamiento al engine. La carga no llegó a completarse; estos datos no prueban el pico de una inferencia ni la calidad de audio.

## Custodia y límites

El sampler y el cliente HTTP de la precarga conservaron identidad propia y terminaron `CLOSED_CONFIRMED`, con recursos devueltos y Job vacío. El motor persistente quedó `idle`, sin modelo ni job; mismo contenedor, imagen y PID padre. Ollama permaneció vacío, la CLI volvió a 1022 MiB y la reserva privada se liberó. No se reconstruyó ni detuvo el contenedor persistente.

Los errores de tres arneses CPU previos están conservados. El primer constructor falló antes de que el arnés retuviera la identidad del hijo: su booleano de limpieza era vacuo. La ausencia posterior de procesos conocidos no sustituye ese recibo perdido. Esta limitación no se oculta ni se atribuye al intento GPU, que sí tiene custodia acreditada.

El cliente retuvo un hash del mensaje de error, pero no el cuerpo HTTP exacto. El 504 se identifica desde el log original; todavía no demuestra la causa del timeout o un OOM. No se repite la precarga a ciegas: el siguiente diagnóstico inspecciona, sin efectos GPU, la versión real del supervisor y la frontera de preparación/copia/carga dentro de la imagen vigente.

## Pendiente

Quedan por probar la causa del desacuerdo histórico, una ventana estable segura y la matriz completa de T-09. Los cuatro resultados anteriores no se convierten en 160 ni en una elección de modelo. Este informe añade evidencia de diagnóstico, sin cerrar el benchmark o el hito.

## Diagnóstico posterior del 504, sin carga GPU

Se extrajeron diez fuentes como texto de la imagen efectiva en ejecución. La ruta de precarga no lleva un deadline en la petición y utiliza el timeout de 60 segundos de `ProcessSupervisor.load`; los jobs, en cambio, trasladan su deadline a la carga. El log original confirma HTTP 504 y el hash del error del cliente coincide con `ApiError: TIMEOUT`. No es sólo un timeout de transporte del arnés. El intervalo entre primera muestra de carga y 504 es 60,443409 s, sin acreditar el instante exacto de entrada al supervisor.

El hijo no emite fases intermedias por IPC y su stderr va a `DEVNULL`. Falta la traza de su fase y su identidad/exit code originales. La verificación de componentes precede a la importación de torch y el lock selecciona 7.709.380.305 bytes, pero no se cronometró ni volvió a ejecutar ese hashing. La ruta local observada no copia pesos. Estos hechos no demuestran cuál fue el coste dominante ni que el hijo no llegara a CUDA.

Una carga real anterior aceptada tardó 122,866 s con otra imagen. Es un antecedente de carga superior a 60 s, no una reproducción del caso actual; su petición exacta no está retenida. No justifica aumentar a ciegas el presupuesto de esta precarga.

El arnés privado de HTTP pasó cuatro comprobaciones CPU: envelope, status/body 504 completo, comportamiento del cliente anterior y rechazo de payload inválido. Su proceso/hilo propios se cerraron. El orquestador verificó 50 artefactos entre ambas entregas, terminal 0 y hash exacto del error, a las 19:22:53 UTC. Recibos en `.cache/dev-cycle/t09/native-nvml-load-probe-20261010/http504-analysis/`; no hay nuevas precargas ni cambios de producto. El siguiente paso de diagnóstico requiere milestones y custodia de carga antes de repetir una ventana GPU.
