# T-09: cancelación por discrepancia de memoria dedicada

La sesión `01M4KG1EQ2D9TEWFEZYR4RRV19` termina incompleta después del piloto y cuatro filas. El audit registra `observability_lost_auto_dedicated_disagreement`, 939 recibos aceptados y 940 intentos. La operación siguiente observa `worker_pipe_eof` tras la cancelación. El recovery confirma cierre del worker propio, retirada de su contenedor, liberación de reserva y restauración del estado previo vacío de Ollama.

## Causa comprobada y límite

Un replay CPU de los tres originales del intento 940 reproduce el rechazo de contraste dedicado. Sus diferencias WDDM/NVML son **259,0078 / 307,0039 / 215 MiB**, frente a la tolerancia aplicable de 128 MiB. Se verifican los hashes canónicos de cada RAW y los cuatro módulos de producto contra el contexto original.

La prueba nativa CPU usa un proceso Windows propio: el sampler falla, `ContinuousCoordinator._fail` termina su Job y el lector observa EOF/exit 1. El proceso queda `CLOSED_CONFIRMED`, con recursos devueltos. El rechazo original se registra antes del EOF. Así se prueba la cadena de cancelación; no un fallo del motor musical.

**El origen físico de la discrepancia entre las APIs no está probado.** Los tres valores crecen durante la carga y las consultas se completan en momentos distintos. Esa observación permite investigar una transición, pero no demuestra caché PDH, error del driver, equivalencia entre fuentes ni desbordamiento. El guard cumple su política actual; no hay un patch de producto justificado y no se amplían tolerancias.

Los cuatro `row.json` tienen `valid=true` y `shared_gpu_observed=true`, aunque el engine informa `spilled_engine=false`. La primera bandera mide memoria compartida agregada del adaptador y no atribuye causalidad al proceso. Tampoco se usa la segunda como prueba de ausencia de spill. Estas cuatro filas no sustituyen la matriz de 160 ni una decisión de calidad musical.

## Sonda de latencia en reposo

Preflight nuevo: Ollama vacío; NVML 1.023 MiB. Una sonda de solo lectura compara 30 veces la API NVML directa instalada, PDH y el proveedor CLI actual. No carga modelos, realiza inferencia ni crea contexto CUDA.

| Consulta | Mediana | Máximo |
|---|---:|---:|
| NVML directa anterior | 0,0110 ms | 0,0179 ms |
| PDH | 0,1044 ms | 0,4794 ms |
| NVML directa posterior | 0,0035 ms | 0,0080 ms |
| CLI nvidia-smi | 31,1733 ms | 40,2860 ms |

La sonda prueba una diferencia de latencia en reposo. **No prueba que NVML directa resuelva la discrepancia durante carga.** No se cambia el proveedor, la política, el contexto de las sesiones anteriores ni sus recibos. El siguiente experimento debe contrastar captura durante una carga acotada y autorizada, conservando los originales y todos los límites. No se repite una matriz completa a ciegas.

## Evidencia y estado

Directorio privado `.cache/dev-cycle/t09/worker-eof-sync2-diagnosis-20261010/`: `diagnosis.md`, `cpu-probe-result.json`, `temporal-comparison.json`, `root-verification.json` y `native-nvml-idle-probe.json`. Root repite el replay de los tres originales, coteja cuatro hashes y las cuatro filas, con exit 0. No vuelve a ejecutar ni sobrescribe el proceso CPU histórico.

T-09 sigue `en-progreso`. Debug-root-cause termina en fases 1–3; fase 4 no iniciada, pues no existe fix ni causa física demostrada. No se propone un gotcha de una causa no demostrada. Esta evidencia no cierra M0, M1 ni el objetivo global.
